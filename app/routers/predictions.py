from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.firebase_config import get_ref
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import re
router = APIRouter(prefix="/predict", tags=["Predictions"])

# Loading the trained model
model = joblib.load("models/patient_risk_model.pkl")

# Pakistan Standard Time (UTC+5)
PST = timezone(timedelta(hours=5))

def get_pst_now():
    """Get current time in Pakistan Standard Time"""
    return datetime.now(PST)



def format_datetime_for_firebase(dt):
    """Format datetime in a Firebase-safe format (no colons or special chars)"""
    return dt.strftime("%Y-%m-%d_%H-%M-%S")

def get_latest_vitals(patient_id: str) -> Optional[dict]:
    """Fetch latest vitals for a patient from IoT monitors using new schema"""
    try:
        print(f"Getting latest vitals for patient: {patient_id}")
        # Get all IoT devices
        iot_ref = get_ref('iotData')
        monitors = iot_ref.get()
        
        print(f"Found {len(monitors) if monitors else 0} monitors")
        
        if not monitors:
            print("No monitors found in database")
            return None
        
        # Find monitor assigned to patient and get latest vitals
        latest_vitals = None
        latest_timestamp = None
        
        for monitor_id, data in monitors.items():
            print(f"Checking monitor: {monitor_id}")
            device_info = data.get('deviceInfo', {})
            
            # Check if this is a vitals monitor
            if device_info.get('type') != 'vitals_monitor':
                print(f"Monitor {monitor_id} is not a vitals monitor: {device_info.get('type')}")
                continue
                
            # Check if patient is currently assigned to this monitor
            current_patient_id = device_info.get('currentPatientId')
            print(f"Monitor {monitor_id} current patient: {current_patient_id}")
            
            if current_patient_id == patient_id:
                print(f"Found assigned monitor {monitor_id} for patient {patient_id}")
                # Get vitals for this patient using new structure: vitals/{patient_id}/{timestamp}
                vitals_data = data.get('vitals', {}).get(patient_id, {})
                
                print(f"Vitals data keys for patient: {list(vitals_data.keys()) if vitals_data else 'None'}")
                
                if vitals_data:
                    # Find the latest timestamp
                    for timestamp, vitals in vitals_data.items():
                        print(f"Checking timestamp: {timestamp}")
                        if latest_timestamp is None or timestamp > latest_timestamp:
                            latest_timestamp = timestamp
                            latest_vitals = vitals
                            print(f"Updated latest vitals from timestamp: {timestamp}")
        
        print(f"Returning vitals: {latest_vitals is not None}")
        return latest_vitals
    except Exception as e:
        print(f"Error in get_latest_vitals: {str(e)}")
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
        timestamp = get_pst_now()
        timestamp_str = format_datetime_for_firebase(timestamp)
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
            "timestamp": timestamp_str,
            "processingTime": 0.0,  # TODO: Add actual processing time measurement
            "feedback": None  # Will be updated when staff provides feedback
        }
        
        # Store in AI logs with timestamp-based key
        ai_logs_ref = get_ref(f'aiLogs/{patient_id}/{timestamp_str}')
        ai_logs_ref.set(log_entry)
        
        # Also store in patient's predictions history
        predictions_history_ref = get_ref(f'patients/{patient_id}/predictionsHistory/{timestamp_str}')
        predictions_history_ref.set(prediction_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging prediction: {str(e)}")

def create_alert(patient_id: str, risk_level: str, risk_score: int, vitals: dict, monitor_id: str):
    """Create an alert in the patient's monitor"""
    try:
        timestamp = datetime.now()
        timestamp_str = format_datetime_for_firebase(timestamp)
        alert_message = f"High Risk Alert: Patient risk level {risk_level} (Score: {risk_score}%)"
        if risk_level == "Critical":
            alert_type = "critical"
        else:
            alert_type = "warning"
            
        # Create alert details
        alert = {
            "type": alert_type,
            "message": alert_message,
            "timestamp": timestamp_str,
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
        monitor_ref = get_ref(f'iotData/{monitor_id}/alerts/{timestamp_str}')
        monitor_ref.set(alert)
        
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
        central_alerts_ref = get_ref(f'alerts/{timestamp_str}')
        central_alerts_ref.set(central_alert)
        
        # logger.info(f"Created {alert_type} alert for patient {patient_id}") # logger is not defined
        return timestamp_str
        
    except Exception as e:
        # logger.error(f"Error creating alert: {str(e)}") # logger is not defined
        return None

def get_patient_monitor(patient_id: str) -> tuple[Optional[str], Optional[dict]]:
    """Find the monitor assigned to a patient and get its latest vitals using new schema"""
    try:
        print(f"Finding monitor for patient: {patient_id}")
        iot_ref = get_ref('iotData')
        monitors = iot_ref.get()
        
        print(f"Retrieved {len(monitors) if monitors else 0} monitors from database")
        
        if not monitors:
            print("No monitors found in database")
            return None, None
        
        for monitor_id, data in monitors.items():
            print(f"Examining monitor: {monitor_id}")
            device_info = data.get('deviceInfo', {})
            
            # Check if this is a vitals monitor
            if device_info.get('type') != 'vitals_monitor':
                print(f"Skipping monitor {monitor_id} - not a vitals monitor: {device_info.get('type')}")
                continue
                
            # Check if patient is currently assigned to this monitor
            current_patient_id = device_info.get('currentPatientId')
            print(f"Monitor {monitor_id} current patient: {current_patient_id}")
            
            if current_patient_id == patient_id:
                print(f"Found matching monitor {monitor_id} for patient {patient_id}")
                # Get vitals for this patient using new structure: vitals/{patient_id}/{timestamp}
                vitals_data = data.get('vitals', {}).get(patient_id, {})
                
                print(f"Vitals data structure: {list(vitals_data.keys()) if vitals_data else 'No vitals data'}")
                
                if vitals_data:
                    # Find the latest timestamp and vitals
                    latest_timestamp = None
                    latest_vitals = None
                    
                    for timestamp, vitals in vitals_data.items():
                        print(f"Checking vitals timestamp: {timestamp}")
                        if latest_timestamp is None or timestamp > latest_timestamp:
                            latest_timestamp = timestamp
                            latest_vitals = vitals
                            print(f"Updated latest vitals from: {timestamp}")
                    
                    if latest_vitals:
                        print(f"Returning monitor {monitor_id} with vitals from {latest_timestamp}")
                        return monitor_id, latest_vitals
                else:
                    print(f"Monitor {monitor_id} has no vitals data for patient {patient_id}")
                
        print(f"No suitable monitor found for patient {patient_id}")
        return None, None
    except Exception as e:
        print(f"Error in get_patient_monitor: {str(e)}")
        return None, None

@router.get("/risk/{patient_id}")
def predict_risk(patient_id: str):
    try:
        print(f"Starting risk prediction for patient: {patient_id}")
        start_time = datetime.now()
        
        # Find patient's monitor and get latest vitals
        print(f"Finding monitor for patient: {patient_id}")
        monitor_id, vitals = get_patient_monitor(patient_id)
        
        print(f"Monitor found: {monitor_id}, Vitals found: {vitals is not None}")
        
        if not vitals:
            print(f"No vitals found for patient {patient_id}")
            raise HTTPException(status_code=404, detail="No recent vitals found for patient")
        
        if not monitor_id:
            print(f"No monitor found for patient {patient_id}")
            raise HTTPException(status_code=404, detail="No monitor found for patient")
        
        # Fetch patient info
        print(f"Fetching patient info for: {patient_id}")
        patient_info = get_patient_info(patient_id)
        print(f"Patient info retrieved: {patient_info is not None}")
        
        # Extract medical conditions
        conditions = patient_info.get("medicalHistory", {}).get("conditions", [])
        print(f"Medical conditions found: {conditions}")
        
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
        
        print(f"Features prepared: {features_dict}")
        
        features = pd.DataFrame([features_dict])
        print(f"DataFrame created with shape: {features.shape}")
        
        # Making prediction
        print("Making prediction with model...")
        prediction = model.predict(features)[0]
        probabilities = model.predict_proba(features)[0]
        max_prob = float(np.max(probabilities))
        
        print(f"Prediction: {prediction}, Max probability: {max_prob}")

        # Getting class names
        class_names = model.named_steps['classifier'].classes_
        prob_dict = {class_name: float(prob) for class_name, prob in zip(class_names, probabilities)}
        
        print(f"Probability distribution: {prob_dict}")
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Generate recommendations based on risk level and vitals
        recommendations = []
        risk_score = int(max_prob * 100)
        
        print(f"Risk score calculated: {risk_score}")
        
        # Create alert for high or critical risk
        alert_id = None
        if prediction in ["High", "Critical"]:
            print(f"Creating alert for {prediction} risk")
            alert_id = create_alert(
                patient_id=patient_id,
                risk_level=prediction,
                risk_score=risk_score,
                vitals=vitals,
                monitor_id=monitor_id
            )
            print(f"Alert created with ID: {alert_id}")
            
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
        
        print(f"Prediction data prepared: {prediction_data}")
        
        # Update current patient predictions
        print("Updating patient predictions...")
        patient_predictions_ref = get_ref(f'patients/{patient_id}/predictions')
        patient_predictions_ref.set(prediction_data)
        
        # Log the prediction with input data
        print("Logging prediction...")
        log_prediction(patient_id, prediction_data, features_dict)
        
        print("Risk prediction completed successfully")
        
        return {
            "patient_id": patient_id,
            "prediction": prediction,
            "probabilities": prob_dict,
            "prediction_details": prediction_data,
            "alert_created": alert_id is not None
        }

    except HTTPException as he:
        print(f"HTTP Exception: {he.detail}")
        raise he
    except Exception as e:
        print(f"Unexpected error in risk prediction: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

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