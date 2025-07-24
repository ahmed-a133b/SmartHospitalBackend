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
    """Fetch latest vitals for a patient from IoT monitors using new schema"""
    try:
        # Get all IoT devices
        iot_ref = get_ref('iotData')
        monitors = iot_ref.get()
        if not monitors:
            return None
        
        # Find monitor assigned to patient and get latest vitals
        latest_vitals = None
        latest_timestamp = None
        
        for monitor_id, data in monitors.items():
            device_info = data.get('deviceInfo', {})
            
            # Check if this is a vitals monitor
            if device_info.get('type') != 'vitals_monitor':
                continue
                
            # Check if patient is currently assigned to this monitor
            current_patient_id = device_info.get('currentPatientId')
            if current_patient_id == patient_id:
                # Get vitals for this patient using new structure: vitals/{patient_id}/{timestamp}
                vitals_data = data.get('vitals', {}).get(patient_id, {})
                
                if vitals_data:
                    # Find the latest timestamp
                    for timestamp, vitals in vitals_data.items():
                        if latest_timestamp is None or timestamp > latest_timestamp:
                            latest_timestamp = timestamp
                            latest_vitals = vitals
        
        return latest_vitals
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
    """Find the monitor assigned to a patient and get its latest vitals using new schema"""
    try:
        iot_ref = get_ref('iotData')
        monitors = iot_ref.get()
        if not monitors:
            return None, None
        
        for monitor_id, data in monitors.items():
            device_info = data.get('deviceInfo', {})
            
            # Check if this is a vitals monitor
            if device_info.get('type') != 'vitals_monitor':
                continue
                
            # Check if patient is currently assigned to this monitor
            current_patient_id = device_info.get('currentPatientId')
            if current_patient_id == patient_id:
                # Get vitals for this patient using new structure: vitals/{patient_id}/{timestamp}
                vitals_data = data.get('vitals', {}).get(patient_id, {})
                
                if vitals_data:
                    # Find the latest timestamp and vitals
                    latest_timestamp = None
                    latest_vitals = None
                    
                    for timestamp, vitals in vitals_data.items():
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

@router.get("/test-vitals/{patient_id}")
def test_vitals_retrieval(patient_id: str):
    """Test endpoint to verify vitals retrieval with new schema"""
    try:
        # Test the updated vitals retrieval functions
        monitor_id, latest_vitals = get_patient_monitor(patient_id)
        
        if not monitor_id or not latest_vitals:
            return {
                "patient_id": patient_id,
                "monitor_found": False,
                "vitals_found": False,
                "message": "No monitor assigned to patient or no vitals available"
            }
        
        # Also test the alternative function
        alt_vitals = get_latest_vitals(patient_id)
        
        return {
            "patient_id": patient_id,
            "monitor_found": True,
            "monitor_id": monitor_id,
            "vitals_found": True,
            "latest_vitals": latest_vitals,
            "alt_vitals_match": alt_vitals == latest_vitals,
            "vitals_structure": {
                "heartRate": latest_vitals.get('heartRate'),
                "bloodPressure": latest_vitals.get('bloodPressure'),
                "oxygenLevel": latest_vitals.get('oxygenLevel'),
                "temperature": latest_vitals.get('temperature'),
                "respiratoryRate": latest_vitals.get('respiratoryRate'),
                "glucose": latest_vitals.get('glucose'),
                "timestamp": latest_vitals.get('timestamp'),
                "patientId": latest_vitals.get('patientId')
            }
        }
        
    except Exception as e:
        return {
            "patient_id": patient_id,
            "error": str(e),
            "monitor_found": False,
            "vitals_found": False
        }

@router.get("/debug/monitors")
def debug_monitor_structure():
    """Debug endpoint to show the current monitor data structure"""
    try:
        iot_ref = get_ref('iotData')
        monitors = iot_ref.get()
        
        if not monitors:
            return {"message": "No monitors found"}
        
        debug_info = {}
        
        for monitor_id, data in monitors.items():
            device_info = data.get('deviceInfo', {})
            vitals_structure = data.get('vitals', {})
            
            debug_info[monitor_id] = {
                "device_type": device_info.get('type'),
                "current_patient": device_info.get('currentPatientId'),
                "room_id": device_info.get('roomId'),
                "bed_id": device_info.get('bedId'),
                "vitals_patients": list(vitals_structure.keys()) if vitals_structure else [],
                "vitals_count_by_patient": {
                    patient_id: len(patient_vitals) 
                    for patient_id, patient_vitals in vitals_structure.items()
                } if vitals_structure else {}
            }
        
        return {
            "total_monitors": len(monitors),
            "monitors": debug_info
        }
        
    except Exception as e:
        return {"error": str(e)}