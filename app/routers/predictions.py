from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.firebase_config import get_ref
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional

router = APIRouter(prefix="/predict", tags=["Predictions"])

# Loading the trained model
model = joblib.load("models/patient_risk_model.pkl")

def format_datetime_for_firebase(dt):
    """Format datetime in a Firebase-safe format (no colons or special chars)"""
    return dt.strftime("%Y-%m-%d_%H-%M-%S")

def get_latest_vitals(patient_id: str) -> Optional[dict]:
    """Fetch latest vitals for a patient from IoT monitors"""
    try:
        # Get all IoT devices
        iot_ref = get_ref('iotData')
        monitors = iot_ref.get()
        if not monitors:
            return None
        
        # Find monitor assigned to patient
        patient_monitor = None
        patient_vitals = None
        latest_timestamp = None
        
        for monitor_id, data in monitors.items():
            if 'vitals' in data:
                # Get the latest vitals entry
                vitals_data = data['vitals']
                for timestamp, vitals in vitals_data.items():
                    if vitals.get('patientId') == patient_id:
                        if latest_timestamp is None or timestamp > latest_timestamp:
                            latest_timestamp = timestamp
                            patient_vitals = vitals
        
        return patient_vitals
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching vitals: {str(e)}")

def get_patient_info(patient_id: str) -> dict:
    """Fetch patient information from database"""
    try:
        patient_ref = get_ref(f'patients/{patient_id}')
        patient_data = patient_ref.get()
        if not patient_data:
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
        return patient_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching patient info: {str(e)}")

def log_prediction(patient_id: str, prediction_data: dict, input_data: dict):
    """Log the prediction in AI logs with timestamp-based key"""
    try:
        current_time = datetime.now()
        timestamp = format_datetime_for_firebase(current_time)
        
        # Create AI log entry
        log_entry = {
            "modelId": "patient_risk_model",
            "modelVersion": "1.0",
            "patientId": patient_id,
            "inputData": {
                "heartRate": input_data.get("heart_rate"),
                "oxygenLevel": input_data.get("oxygen_level"),
                "temperature": input_data.get("temperature"),
                "bloodPressure": {
                    "systolic": input_data.get("systolic_bp"),
                    "diastolic": input_data.get("diastolic_bp")
                },
                "respiratoryRate": input_data.get("respiratory_rate"),
                "contextData": {
                    "age": input_data.get("age"),
                    "conditions": input_data.get("conditions").split("|") if input_data.get("conditions") else []
                }
            },
            "output": {
                "riskLevel": prediction_data.get("riskLevel"),
                "riskScore": prediction_data.get("riskScore"),
                "confidence": prediction_data.get("confidence"),
                "recommendations": prediction_data.get("recommendations", []),
                "alertTriggered": prediction_data.get("riskScore", 0) > 75  # Alert if risk score > 75%
            },
            "timestamp": timestamp,
            "processingTime": 0.0,  # TODO: Add actual processing time measurement
            "feedback": None  # Will be updated when staff provides feedback
        }
        
        # Store in AI logs with timestamp-based key
        ai_logs_ref = get_ref(f'aiLogs/{patient_id}/{timestamp}')
        ai_logs_ref.set(log_entry)
        
        # Also store in patient's predictions history
        predictions_history_ref = get_ref(f'patients/{patient_id}/predictionsHistory/{timestamp}')
        predictions_history_ref.set(prediction_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging prediction: {str(e)}")

def create_alert(patient_id: str, risk_level: str, risk_score: int, vitals: dict, monitor_id: str):
    """Create an alert in the patient's monitor"""
    try:
        current_time = datetime.now()
        timestamp = format_datetime_for_firebase(current_time)
        
        alert_message = f"High Risk Alert: Patient risk level {risk_level} (Score: {risk_score}%)"
        if risk_level == "Critical":
            alert_type = "critical"
        else:
            alert_type = "warning"
            
        # Create alert details
        alert = {
            "type": alert_type,
            "message": alert_message,
            "timestamp": timestamp,
            "resolved": False,
            "resolvedBy": None,
            "resolvedAt": None,
            "vitals": {
                "heartRate": vitals.get('heartRate'),
                "oxygenLevel": vitals.get('oxygenLevel'),
                "temperature": vitals.get('temperature'),
                "bloodPressure": vitals.get('bloodPressure'),
                "respiratoryRate": vitals.get('respiratoryRate')
            }
        }
        
        # Add alert to monitor
        monitor_ref = get_ref(f'iotData/{monitor_id}/alerts')
        monitor_ref.child(timestamp).set(alert)
        
        # Also add to central alerts collection for easier querying
        central_alert = {
            **alert,
            "patientId": patient_id,
            "monitorId": monitor_id,
            "location": {
                "roomId": vitals.get("roomId"),
                "bedId": vitals.get("bedId")
            }
        }
        central_alerts_ref = get_ref('alerts')
        central_alerts_ref.child(timestamp).set(central_alert)
        
        # logger.info(f"Created {alert_type} alert for patient {patient_id}") # logger is not defined
        return timestamp
        
    except Exception as e:
        # logger.error(f"Error creating alert: {str(e)}") # logger is not defined
        return None

def get_patient_monitor(patient_id: str) -> tuple[Optional[str], Optional[dict]]:
    """Find the monitor assigned to a patient and get its latest vitals"""
    try:
        iot_ref = get_ref('iotData')
        monitors = iot_ref.get()
        if not monitors:
            return None, None
        
        for monitor_id, data in monitors.items():
            if 'vitals' not in data:
                continue
                
            # Get the latest vitals entry
            vitals_data = data['vitals']
            latest_timestamp = None
            latest_vitals = None
            
            for timestamp, vitals in vitals_data.items():
                if vitals.get('patientId') == patient_id:
                    if latest_timestamp is None or timestamp > latest_timestamp:
                        latest_timestamp = timestamp
                        latest_vitals = vitals
                        
            if latest_vitals:
                return monitor_id, latest_vitals
                
        return None, None
    except Exception as e:
        # logger.error(f"Error finding patient monitor: {str(e)}") # logger is not defined
        return None, None

@router.get("/risk/{patient_id}")
def predict_risk(patient_id: str):
    try:
        start_time = datetime.now()
        
        # Find patient's monitor and get latest vitals
        monitor_id, vitals = get_patient_monitor(patient_id)
        if not vitals:
            raise HTTPException(status_code=404, detail="No recent vitals found for patient")
        
        if not monitor_id:
            raise HTTPException(status_code=404, detail="No monitor found for patient")
        
        # Fetch patient info
        patient_info = get_patient_info(patient_id)
        
        # Extract medical conditions
        conditions = patient_info.get("medicalHistory", {}).get("conditions", [])
        
        # Prepare features for prediction
        features_dict = {
            "heart_rate": vitals.get('heartRate', 0),
            "oxygen_level": vitals.get('oxygenLevel', 0),
            "temperature": vitals.get('temperature', 0),
            "systolic_bp": vitals.get('bloodPressure', {}).get('systolic', 0),
            "diastolic_bp": vitals.get('bloodPressure', {}).get('diastolic', 0),
            "age": patient_info.get('personalInfo', {}).get('age', 0),
            "glucose": vitals.get('glucose', 0),
            "respiratory_rate": vitals.get('respiratoryRate', 0),
            "num_conditions": len(conditions),
            "conditions": "|".join(conditions) if conditions else ""
        }
        
        features = pd.DataFrame([features_dict])
        
        # Making prediction
        prediction = model.predict(features)[0]
        probabilities = model.predict_proba(features)[0]
        max_prob = float(np.max(probabilities))

        # Getting class names
        class_names = model.named_steps['classifier'].classes_
        prob_dict = {class_name: float(prob) for class_name, prob in zip(class_names, probabilities)}
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Generate recommendations based on risk level and vitals
        recommendations = []
        risk_score = int(max_prob * 100)
        
        # Create alert for high or critical risk
        alert_id = None
        if prediction in ["High", "Critical"]:
            alert_id = create_alert(
                patient_id=patient_id,
                risk_level=prediction,
                risk_score=risk_score,
                vitals=vitals,
                monitor_id=monitor_id
            )
            
            if prediction == "Critical":
                recommendations.append("Immediate medical attention required")
                if vitals.get('heartRate', 0) > 100:
                    recommendations.append("Monitor heart rate closely")
                if vitals.get('oxygenLevel', 0) < 95:
                    recommendations.append("Check oxygen supplementation")
            else:  # High risk
                recommendations.append("Increase monitoring frequency")
                if len(conditions) > 2:
                    recommendations.append("Review medication interactions")
        elif risk_score > 50:  # Moderate risk
            recommendations.append("Regular monitoring required")
            if len(conditions) > 2:
                recommendations.append("Review medication plan")
        
        # Prepare prediction data
        prediction_data = {
            'riskLevel': prediction,
            'riskScore': risk_score,
            'confidence': max_prob,
            'predictedAt': format_datetime_for_firebase(datetime.now()),
            'nextPrediction': format_datetime_for_firebase(datetime.now() + timedelta(hours=4)),
            'factors': conditions,
            'recommendations': recommendations,
            'vitalsUsed': {
                'heartRate': vitals.get('heartRate'),
                'oxygenLevel': vitals.get('oxygenLevel'),
                'temperature': vitals.get('temperature'),
                'bloodPressure': vitals.get('bloodPressure'),
                'respiratoryRate': vitals.get('respiratoryRate'),
                'glucose': vitals.get('glucose')
            },
            'processingTime': processing_time,
            'alertId': alert_id
        }
        
        # Update current patient predictions
        patient_predictions_ref = get_ref(f'patients/{patient_id}/predictions')
        patient_predictions_ref.set(prediction_data)
        
        # Log the prediction with input data
        log_prediction(patient_id, prediction_data, features_dict)
        
        return {
            "patient_id": patient_id,
            "prediction": prediction,
            "probabilities": prob_dict,
            "prediction_details": prediction_data,
            "alert_created": alert_id is not None
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        # logger.error(f"Error in risk prediction: {str(e)}") # logger is not defined
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")