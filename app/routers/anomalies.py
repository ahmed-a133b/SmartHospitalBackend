# app/routers/anomalies.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
import joblib
import numpy as np
import os
import re
from app.firebase_config import get_ref

router = APIRouter(prefix="/anomalies", tags=["Anomaly Detection"])
logger = logging.getLogger(__name__)

# def sanitize_timestamp(timestamp):
#         # Convert ISO timestamp to a Firebase-safe string
#         # Replace colons, periods, and other invalid characters
#         sanitized = re.sub(r'[.:]', '-', timestamp)
#         # Remove any other invalid characters for Firebase paths
#         sanitized = re.sub(r'[#\$\[\]]', '', sanitized)
#         return sanitized

def format_datetime_for_firebase(dt):
    """Format datetime in a Firebase-safe format (no colons or special chars)"""
    return dt.strftime("%Y-%m-%d_%H-%M-%S")

def format_timestamp_string_for_firebase(timestamp_str):
    """Format ISO timestamp string to Firebase-safe format"""
    try:
        # Handle different ISO formats
        if isinstance(timestamp_str, str):
            # Remove timezone info and parse
            clean_timestamp = timestamp_str.replace('Z', '').replace('+00:00', '')
            if 'T' in clean_timestamp:
                dt = datetime.fromisoformat(clean_timestamp)
            else:
                # Try to parse as standard datetime string
                dt = datetime.strptime(clean_timestamp, "%Y-%m-%d %H:%M:%S")
            return format_datetime_for_firebase(dt)
        else:
            # If it's already a datetime object
            return format_datetime_for_firebase(timestamp_str)
    except Exception as e:
        logger.warning(f"Could not parse timestamp {timestamp_str}, using sanitized version: {e}")
        # Fallback: sanitize the string directly
        sanitized = re.sub(r'[.:]', '-', str(timestamp_str))
        sanitized = re.sub(r'[#\$\[\]TZ+]', '', sanitized)
        return sanitized

# Load the trained anomaly model
def load_anomaly_model():
    """Load the trained isolation forest anomaly model"""
    try:
        # Get the models directory path
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_path = os.path.join(current_dir, 'models', 'isolation_forest_anomaly_model.pkl')
        
        if os.path.exists(model_path):
            model_data = joblib.load(model_path)
            logger.info(f"Anomaly model loaded successfully from {model_path}")
            return model_data
        else:
            logger.warning(f"Anomaly model not found at {model_path}")
            return None
    except Exception as e:
        logger.error(f"Error loading anomaly model: {e}")
        return None

# Load model on startup
anomaly_model_data = load_anomaly_model()

def detect_anomaly_with_model(sensor_data: Dict, device_id: str, environmental_data: Optional[Dict] = None) -> Dict:
    """
    Detect anomalies using the trained Isolation Forest model
    Includes environmental data if provided
    """
    timestamp = datetime.now().isoformat()
    
    # Initialize result
    result = {
        "device_id": device_id,
        "timestamp": timestamp,
        "is_anomaly": False,
        "anomaly_score": 0.0,
        "severity_level": "NORMAL",
        "severity_score": 0.0,
        "anomaly_type": [],
        "details": {},
        "confidence": 0.0,
        "environmental_included": environmental_data is not None
    }
    
    if anomaly_model_data is None:
        logger.warning("Anomaly model not loaded, skipping anomaly detection")
        result["details"]["model_status"] = "Model not available - no detection performed"
        result["severity_level"] = "NORMAL"
        return result
    
    try:
        model = anomaly_model_data['model']
        scaler = anomaly_model_data['scaler']
        feature_names = anomaly_model_data['feature_names']
        
        logger.info(f"Processing anomaly detection for device {device_id} with features: {list(sensor_data.keys())}")
        if environmental_data:
            logger.info(f"Including environmental data: {list(environmental_data.keys())}")
        
        # Combine sensor data and environmental data
        combined_data = sensor_data.copy()
        
        # Map Firebase vital signs to model feature names
        vital_mapping = {
            'heartRate': 'heart_rate',
            'oxygenLevel': 'oxygen_level',
            'respiratoryRate': 'respiratory_rate',
            'temperature': 'temperature',
            'glucose': 'glucose'
        }
        
        # Create a properly mapped dataset for the model
        mapped_data = {}
        for fb_key, model_key in vital_mapping.items():
            if fb_key in sensor_data:
                mapped_data[model_key] = sensor_data[fb_key]
        
        # Handle blood pressure mapping (it's an object in Firebase)
        if 'bloodPressure' in sensor_data and isinstance(sensor_data['bloodPressure'], dict):
            bp = sensor_data['bloodPressure']
            mapped_data['systolic_bp'] = bp.get('systolic', 0)
            mapped_data['diastolic_bp'] = bp.get('diastolic', 0)
        
        if environmental_data:
            # Add environmental data with appropriate field mapping
            env_mapping = {
                'temperature': 'env_temperature',
                'humidity': 'env_humidity', 
                'airQuality': 'env_air_quality',
                'lightLevel': 'env_light_level',
                'noiseLevel': 'env_noise_level',
                'pressure': 'env_pressure',
                'co2Level': 'env_co2_level'
            }
            
            for env_key, model_key in env_mapping.items():
                if env_key in environmental_data:
                    mapped_data[model_key] = environmental_data[env_key]
        
        # Use mapped_data instead of combined_data for feature extraction
        combined_data = mapped_data
        
        logger.info(f"Mapped data for model: {combined_data}")
        
        # Prepare features in the same order as training
        features = []
        for feature_name in feature_names:
            value = combined_data.get(feature_name, 0)
            # Ensure value is a Python float, not numpy type
            features.append(float(value) if value is not None else 0.0)
        
        logger.info(f"Prepared features: {features}")
        logger.info(f"Feature names: {feature_names}")
        
        # Convert to numpy array and reshape
        features_array = np.array(features, dtype=np.float64).reshape(1, -1)
        
        # Scale features
        features_scaled = scaler.transform(features_array)
        
        # Get prediction and anomaly score
        prediction = model.predict(features_scaled)[0]
        anomaly_score = model.decision_function(features_scaled)[0]
        
        # Update result (convert numpy types to Python types)
        result["anomaly_score"] = float(anomaly_score)
        result["is_anomaly"] = bool(prediction == -1)
        result["confidence"] = float(abs(anomaly_score))
        
        if result["is_anomaly"]:
            # Analyze which type of anomaly this is based on feature values
            anomaly_types = []
            
            # Check vital sign anomalies using mapped field names
            hr = combined_data.get('heart_rate', 70)
            sys_bp = combined_data.get('systolic_bp', 120)
            dia_bp = combined_data.get('diastolic_bp', 80)
            temp = combined_data.get('temperature', 37)
            o2 = combined_data.get('oxygen_level', 98)
            rr = combined_data.get('respiratory_rate', 16)
            glucose = combined_data.get('glucose', 100)
            
            # Cardiac anomalies
            if hr > 110 or hr < 50:
                anomaly_types.append("Cardiac Rhythm Anomaly")
            if sys_bp > 160 or sys_bp < 90 or dia_bp > 100 or dia_bp < 60:
                anomaly_types.append("Blood Pressure Anomaly")
            
            # Respiratory anomalies
            if o2 < 95 or rr > 25 or rr < 10:
                anomaly_types.append("Respiratory Anomaly")
            
            # Temperature anomalies
            if temp > 38.5 or temp < 35.5:
                anomaly_types.append("Temperature Anomaly")
            
            # Metabolic anomalies
            if glucose > 180 or glucose < 70:
                anomaly_types.append("Metabolic Anomaly")
            
            # Environmental anomalies (if environmental data included)
            if environmental_data:
                env_temp = combined_data.get('env_temperature', 22)
                env_humidity = combined_data.get('env_humidity', 45)
                env_air_quality = combined_data.get('env_air_quality', 85)
                env_noise = combined_data.get('env_noise_level', 35)
                env_co2 = combined_data.get('env_co2_level', 400)
                
                if env_temp > 26 or env_temp < 18 or env_humidity > 70 or env_humidity < 30:
                    anomaly_types.append("Environmental Climate Anomaly")
                if env_air_quality < 60 or env_co2 > 800:
                    anomaly_types.append("Air Quality Anomaly")
                if env_noise > 60:
                    anomaly_types.append("Noise Level Anomaly")
            
            # If no specific anomaly type found, use general classification
            if not anomaly_types:
                anomaly_types.append("Statistical Outlier")
            
            result["anomaly_type"] = anomaly_types
            
            # Adjust severity based on anomaly score - make thresholds more restrictive
            if float(anomaly_score) < -0.5:  # Very restrictive threshold for HIGH
                result["severity_level"] = "HIGH"
                result["severity_score"] = float(abs(anomaly_score)) * 10
            elif float(anomaly_score) < -0.35:  # More restrictive for MEDIUM
                result["severity_level"] = "MEDIUM" 
                result["severity_score"] = float(abs(anomaly_score)) * 8
            else:  # Less severe anomalies
                result["severity_level"] = "LOW"
                result["severity_score"] = float(abs(anomaly_score)) * 5
        
        # Add confidence assessment to details
        result["details"]["confidence_assessment"] = "High" if result["confidence"] > 0.5 else "Medium" if result["confidence"] > 0.2 else "Low"
        result["details"]["model_status"] = "Model loaded and functional"
        
        # Ensure all numeric values are JSON serializable Python types
        result["anomaly_score"] = float(result["anomaly_score"])
        result["severity_score"] = float(result["severity_score"])
        result["confidence"] = float(result["confidence"])
        result["is_anomaly"] = bool(result["is_anomaly"])
        
    except Exception as e:
        logger.error(f"Error in model-based anomaly detection: {e}")
        result["details"]["model_error"] = str(e)
        result["severity_level"] = "NORMAL"
        result["details"]["model_status"] = "Model error - no detection performed"
        return result
    
    return result

class AnomalyAlert(BaseModel):
    device_id: str
    timestamp: str
    severity_level: str
    anomaly_type: List[str]
    message: str
    resolved: bool = False

def get_recent_vitals(device_id: str, hours: int = 1) -> List[Dict]:
    """Get recent vitals for trend analysis"""
    try:
        # First get the device to check current patient assignment
        device_ref = get_ref(f"iotData/{device_id}")
        device_data = device_ref.get()
        
        if not device_data:
            logger.warning(f"Device {device_id} not found")
            return []
        
        # Get current patient ID
        current_patient_id = device_data.get("deviceInfo", {}).get("currentPatientId")
        
        if not current_patient_id:
            logger.warning(f"No patient assigned to device {device_id}")
            return []
        
        # Get vitals for the current patient
        vitals_ref = get_ref(f"iotData/{device_id}/vitals/{current_patient_id}")
        vitals_data = vitals_ref.get() or {}
        
        # Filter by time (last N hours)
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_vitals = []
        
        for timestamp, data in vitals_data.items():
            try:
                # Parse timestamp (handle sanitized format)
                ts_clean = timestamp.replace('-', ':')
                if '.' in ts_clean:
                    ts_clean = ts_clean.split('.')[0]
                data_time = datetime.fromisoformat(ts_clean)
                
                if data_time >= cutoff_time:
                    recent_vitals.append(data)
            except Exception as e:
                logger.warning(f"Error parsing timestamp {timestamp}: {e}")
                continue
        
        # Sort by timestamp and return last 10 readings
        return recent_vitals[-10:] if recent_vitals else []
    
    except Exception as e:
        logger.error(f"Error getting recent vitals for {device_id}: {e}")
        return []

def save_anomaly_log(anomaly_result: Dict):
    """Save anomaly detection result to Firebase"""
    try:
        device_id = anomaly_result["device_id"]
        timestamp = anomaly_result["timestamp"]
        
        # Sanitize timestamp for Firebase (handle string timestamp)
        safe_timestamp = format_timestamp_string_for_firebase(timestamp)
        
        # Save to anomaly logs
        anomaly_ref = get_ref(f"anomalies/{device_id}/{safe_timestamp}")
        anomaly_ref.set(anomaly_result)
        
        # If it's an anomaly, also save as an alert
        if anomaly_result["is_anomaly"]:
            alert_data = {
                "device_id": device_id,
                "timestamp": timestamp,
                "severity_level": anomaly_result["severity_level"],
                "severity_score": anomaly_result["severity_score"],
                "anomaly_type": anomaly_result["anomaly_type"],
                "message": generate_alert_message(anomaly_result),
                "resolved": False,
                "details": anomaly_result.get("details", {}),
                "trend_analysis": anomaly_result.get("trend_analysis", {})
            }
            
            alert_ref = get_ref(f"iotData/{device_id}/alerts/{safe_timestamp}")
            alert_ref.set(alert_data)
            
            logger.info(f"Anomaly alert created for device {device_id}: {alert_data['severity_level']}")
    
    except Exception as e:
        logger.error(f"Error saving anomaly log: {e}")

def generate_alert_message(anomaly_result: Dict) -> str:
    """Generate human-readable alert message"""
    device_id = anomaly_result["device_id"]
    severity = anomaly_result["severity_level"]
    anomaly_types = anomaly_result["anomaly_type"]
    
    # Format device ID: capitalize first letter and replace underscore with space
    formatted_device_id = device_id.replace("_", " ").capitalize()
    
    if not anomaly_types:
        return f"Anomaly detected for device {formatted_device_id}"
    
    if len(anomaly_types) == 1:
        return f"{severity} Alert: {anomaly_types[0]} detected for device {formatted_device_id}"
    else:
        return f"{severity} Alert: Multiple anomalies detected for device {formatted_device_id}: {', '.join(anomaly_types)}"

@router.get("/model/status")
def get_model_status():
    """
    Get the status of the anomaly detection model
    """
    if anomaly_model_data is None:
        return {
            "model_loaded": False,
            "status": "Model not found or failed to load",
            "features": None,
            "training_samples": None
        }
    
    return {
        "model_loaded": True,
        "status": "Model loaded successfully",
        "features": anomaly_model_data.get('feature_names', []),
        "training_samples": anomaly_model_data.get('training_samples', 0),
        "model_type": "Isolation Forest"
    }

@router.get("/detect/{monitor_id}")
async def detect_anomaly(monitor_id: str, background_tasks: BackgroundTasks = None):
    """
    Detect anomalies for a specific monitor by getting its latest vitals
    Automatically includes environmental sensor data from the same room
    """
    try:
        # Log the received parameters for debugging
        logger.info(f"🔍 Anomaly detection endpoint called for monitor: {monitor_id}")
        
        # Get device data first to check if it exists and has a patient assigned
        device_ref = get_ref(f"iotData/{monitor_id}")
        device_data = device_ref.get()
        
        if not device_data:
            raise HTTPException(status_code=404, detail=f"Monitor {monitor_id} not found")
        
        # Get monitor's room information
        monitor_device_info = device_data.get("deviceInfo", {})
        monitor_room_id = monitor_device_info.get("roomId")
        
        logger.info(f"Monitor {monitor_id} is located in room: {monitor_room_id}")
        
        # Check if a patient is currently assigned to this monitor
        current_patient_id = monitor_device_info.get("currentPatientId")
        
        if not current_patient_id:
            raise HTTPException(status_code=400, detail=f"No patient assigned to monitor {monitor_id}")
        
        # Get vitals for the current patient
        vitals_ref = get_ref(f"iotData/{monitor_id}/vitals/{current_patient_id}")
        patient_vitals = vitals_ref.get() or {}
        
        if not patient_vitals:
            raise HTTPException(status_code=404, detail=f"No vitals data found for patient {current_patient_id} on monitor {monitor_id}")
        
        # Get the most recent reading for this patient
        latest_timestamp = sorted(patient_vitals.keys())[-1]
        latest_vitals = patient_vitals[latest_timestamp]
        
        # Automatically find environmental sensor in the same room
        env_data = None
        env_sensor_id = None
        
        if monitor_room_id:
            try:
                logger.info(f"🔍 Searching for environmental sensor in room {monitor_room_id}")
                
                # Get all IoT devices to find environmental sensor in the same room
                iot_data_ref = get_ref("iotData")
                all_devices = iot_data_ref.get() or {}
                
                logger.info(f"📋 Total devices found: {len(all_devices)}")
                
                # Debug: Log all devices and their room assignments
                for device_id, device_info in all_devices.items():
                    device_details = device_info.get("deviceInfo", {})
                    device_type = device_details.get("type")
                    device_room_id = device_details.get("roomId")
                    
                    logger.debug(f"  Device {device_id}: type={device_type}, roomId={device_room_id}")
                    
                    # Check if this is an environmental sensor in the same room
                    if device_type == "environmental_sensor":
                        logger.info(f"🌡️ Found environmental sensor {device_id} in room {device_room_id}")
                        logger.debug(f"🔍 Device structure keys: {list(device_info.keys())}")
                        
                        if device_room_id == monitor_room_id:
                            env_sensor_id = device_id
                            logger.info(f"✅ Found matching environmental sensor {env_sensor_id} in room {monitor_room_id}")
                            
                            # Get the most recent environmental data 
                            env_vitals = device_info.get("vitals", {})
                            logger.info(f"🔍 Environmental vitals found: {bool(env_vitals)}")
                            if env_vitals:
                                logger.info(f"🔍 Number of vitals timestamps: {len(env_vitals)}")
                                latest_env_timestamp = sorted(env_vitals.keys())[-1]
                                env_data = env_vitals[latest_env_timestamp]
                                logger.info(f"📊 Retrieved environmental data from timestamp: {latest_env_timestamp}")
                                logger.info(f"📊 Environmental data keys: {list(env_data.keys())}")
                            else:
                                logger.warning(f"⚠️ Environmental sensor {env_sensor_id} has no data")
                                logger.warning(f"⚠️ Device info structure: {list(device_info.keys())}")
                            break
                
                if not env_sensor_id:
                    logger.warning(f"⚠️ No environmental sensor found in room {monitor_room_id}")
                    logger.info(f"🔍 Available environmental sensors:")
                    for device_id, device_info in all_devices.items():
                        device_details = device_info.get("deviceInfo", {})
                        if device_details.get("type") == "environmental_sensor":
                            logger.info(f"  - {device_id} in room {device_details.get('roomId', 'NO_ROOM')}")
                    
                    # Fallback: Try to find any environmental sensor if exact room match fails
                    logger.info(f"🔄 Attempting fallback - using any available environmental sensor")
                    for device_id, device_info in all_devices.items():
                        device_details = device_info.get("deviceInfo", {})
                        if device_details.get("type") == "environmental_sensor":
                            env_vitals = device_info.get("vitals", {})
                            if env_vitals:
                                env_sensor_id = device_id
                                latest_env_timestamp = sorted(env_vitals.keys())[-1]
                                env_data = env_vitals[latest_env_timestamp]
                                logger.info(f"🔄 Using fallback environmental sensor {env_sensor_id} (not in same room)")
                                logger.info(f"📊 Fallback environmental data keys: {list(env_data.keys())}")
                                break
                            else:
                                logger.warning(f"⚠️ Environmental sensor {device_id} has no vitals data")
                    
            except Exception as e:
                logger.error(f"❌ Error retrieving environmental data for room {monitor_room_id}: {e}")
        else:
            logger.warning(f"⚠️ Monitor {monitor_id} has no room information")
        
        # Perform anomaly detection with optional environmental data
        anomaly_result = detect_anomaly_with_model(
            sensor_data=latest_vitals,
            device_id=monitor_id,
            environmental_data=env_data
        )
        
        # Add context to the result
        anomaly_result["patient_id"] = current_patient_id
        anomaly_result["vitals_timestamp"] = latest_timestamp
        anomaly_result["room_id"] = monitor_room_id
        anomaly_result["env_sensor_id"] = env_sensor_id
        anomaly_result["env_data_included"] = env_data is not None
        
        if env_data:
            logger.info(f"✅ Anomaly detection completed with environmental data from sensor {env_sensor_id}")
        else:
            logger.info(f"⚠️ Anomaly detection completed without environmental data")
        
        # Save results in background
        background_tasks.add_task(save_anomaly_log, anomaly_result)
        
        return anomaly_result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in anomaly detection: {e}")
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")

@router.get("/{device_id}")
def get_device_anomalies(device_id: str, hours: int = 24):
    """
    Get anomaly history for a specific device
    """
    try:
        anomalies_ref = get_ref(f"anomalies/{device_id}")
        anomalies_data = anomalies_ref.get() or {}
        
        # Filter by time if needed
        if hours < 24 * 30:  # Only filter if less than 30 days
            cutoff_time = datetime.now() - timedelta(hours=hours)
            filtered_anomalies = {}
            
            for timestamp, data in anomalies_data.items():
                try:
                    # Parse timestamp
                    ts_clean = timestamp.replace('-', ':')
                    if '.' in ts_clean:
                        ts_clean = ts_clean.split('.')[0]
                    data_time = datetime.fromisoformat(ts_clean)
                    
                    if data_time >= cutoff_time:
                        filtered_anomalies[timestamp] = data
                except Exception:
                    
                    filtered_anomalies[timestamp] = data
            
            return filtered_anomalies
        
        return anomalies_data
    
    except Exception as e:
        logger.error(f"Error getting anomalies for {device_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get anomalies: {str(e)}")

@router.get("/")
def get_all_anomalies(hours: int = 24, severity_filter: Optional[str] = None):
    """
    Get all anomalies across all devices
    """
    try:
        anomalies_ref = get_ref("anomalies")
        all_anomalies_data = anomalies_ref.get() or {}
        
        result = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for device_id, device_anomalies in all_anomalies_data.items():
            for timestamp, anomaly_data in device_anomalies.items():
                # Time filter
                try:
                    ts_clean = timestamp.replace('-', ':')
                    if '.' in ts_clean:
                        ts_clean = ts_clean.split('.')[0]
                    data_time = datetime.fromisoformat(ts_clean)
                    
                    if data_time < cutoff_time:
                        continue
                except Exception:
                    pass  # Include if timestamp parsing fails
                
                # Severity filter
                if severity_filter and anomaly_data.get("severity_level") != severity_filter.upper():
                    continue
                
                # Only include actual anomalies
                if anomaly_data.get("is_anomaly", False):
                    result.append(anomaly_data)
        
        # Sort by timestamp (most recent first)
        result.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting all anomalies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get anomalies: {str(e)}")

@router.get("/alerts/active")
def get_active_alerts():
    """
    Get all active (unresolved) anomaly alerts
    """
    try:
        iot_data_ref = get_ref("iotData")
        all_devices = iot_data_ref.get() or {}
        
        active_alerts = []
        
        for device_id, device_data in all_devices.items():
            alerts = device_data.get("alerts", {})
            for alert_id, alert in alerts.items():
                if not alert.get("resolved", False):
                    active_alerts.append(alert)
        
        # Sort by severity and timestamp
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        active_alerts.sort(
            key=lambda x: (
                severity_order.get(x.get("severity_level", "LOW"), 4),
                x.get("timestamp", "")
            ),
            reverse=True
        )
        
        return active_alerts
    
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active alerts: {str(e)}")

@router.put("/alerts/{device_id}/{alert_timestamp}/resolve")
def resolve_alert(device_id: str, alert_timestamp: str):
    """
    Mark an alert as resolved
    """
    try:
        alert_ref = get_ref(f"iotData/{device_id}/alerts/{alert_timestamp}")
        alert_data = alert_ref.get()
        
        if not alert_data:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert_data["resolved"] = True
        alert_data["resolved_at"] = datetime.now().isoformat()
        alert_ref.set(alert_data)
        
        return {"message": "Alert resolved successfully"}
    
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")

@router.post("/train")
async def retrain_models(background_tasks: BackgroundTasks):
    """
    Retrain anomaly detection models with recent data
    """
    try:
        def train_models_task():
            # Get recent data from all devices
            iot_data_ref = get_ref("iotData")
            all_devices = iot_data_ref.get() or {}
            
            training_data = []
            
            for device_id, device_data in all_devices.items():
                vitals = device_data.get("vitals", {})
                for timestamp, vital_data in vitals.items():
                    # Only use non-anomalous data for training
                    if isinstance(vital_data, dict):
                        training_data.append(vital_data)
            
            if len(training_data) >= 50:  # Minimum training data
                logger.info(f"Training data collected: {len(training_data)} samples")
                # Note: Model retraining would require running the training script manually
                logger.info("To retrain the model, run the train_anomaly.py script with new data")
            else:
                logger.warning(f"Insufficient training data: {len(training_data)} samples")
        
        background_tasks.add_task(train_models_task)
        
        return {"message": "Model retraining task queued (manual script execution required)"}
    
    except Exception as e:
        logger.error(f"Error starting model retraining: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start retraining: {str(e)}")

@router.get("/statistics")
def get_anomaly_statistics(hours: int = 24):
    """
    Get anomaly detection statistics
    """
    try:
        # Get all anomalies for the time period
        anomalies_ref = get_ref("anomalies")
        all_anomalies_data = anomalies_ref.get() or {}
        
        total_readings = 0
        total_anomalies = 0
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        device_stats = {}
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for device_id, device_anomalies in all_anomalies_data.items():
            device_anomaly_count = 0
            
            for timestamp, anomaly_data in device_anomalies.items():
                # Time filter
                try:
                    ts_clean = timestamp.replace('-', ':')
                    if '.' in ts_clean:
                        ts_clean = ts_clean.split('.')[0]
                    data_time = datetime.fromisoformat(ts_clean)
                    
                    if data_time < cutoff_time:
                        continue
                except Exception:
                    pass
                
                total_readings += 1
                
                if anomaly_data.get("is_anomaly", False):
                    total_anomalies += 1
                    device_anomaly_count += 1
                    
                    severity = anomaly_data.get("severity_level", "LOW")
                    if severity in severity_counts:
                        severity_counts[severity] += 1
            
            if device_id not in device_stats:
                device_stats[device_id] = 0
            device_stats[device_id] += device_anomaly_count
        
        anomaly_rate = (total_anomalies / total_readings * 100) if total_readings > 0 else 0
        
        return {
            "time_period_hours": hours,
            "total_readings": total_readings,
            "total_anomalies": total_anomalies,
            "anomaly_rate_percent": round(anomaly_rate, 2),
            "severity_distribution": severity_counts,
            "device_anomaly_counts": device_stats,
            "engine_status": {
                "model_loaded": anomaly_model_data is not None,
                "model_status": "Available" if anomaly_model_data else "Not loaded"
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting anomaly statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")
