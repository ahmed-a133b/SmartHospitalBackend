# app/routers/anomalies.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
import joblib
import numpy as np
import os

from app.firebase_config import get_ref

router = APIRouter(prefix="/anomalies", tags=["Anomaly Detection"])
logger = logging.getLogger(__name__)

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

def detect_anomaly_with_model(sensor_data: Dict, device_id: str) -> Dict:
    """
    Detect anomalies using the trained Isolation Forest model
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
        "confidence": 0.0
    }
    
    if anomaly_model_data is None:
        logger.warning("Anomaly model not loaded, using rule-based detection only")
        result["details"]["model_status"] = "Model not available"
        return rule_based_detection_only(sensor_data, device_id, result)
    
    try:
        model = anomaly_model_data['model']
        scaler = anomaly_model_data['scaler']
        feature_names = anomaly_model_data['feature_names']
        
        logger.info(f"Processing anomaly detection for device {device_id} with features: {list(sensor_data.keys())}")
        
        # Prepare features in the same order as training
        features = []
        for feature_name in feature_names:
            value = sensor_data.get(feature_name, 0)
            # Ensure value is a Python float, not numpy type
            features.append(float(value) if value is not None else 0.0)
        
        logger.info(f"Prepared features: {features}")
        
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
            result["anomaly_type"].append("Statistical Outlier")
            result["severity_level"] = "HIGH" if float(anomaly_score) < -0.5 else "MEDIUM"
            result["severity_score"] = float(abs(anomaly_score)) * 10
        
        # Also check rule-based thresholds
        rule_result = check_vital_thresholds(sensor_data)
        if rule_result["violations"]:
            result["is_anomaly"] = True
            result["anomaly_type"].extend(rule_result["violations"])
            result["details"]["rule_violations"] = rule_result["details"]
            
            # Update severity based on rule violations
            if any("Critical" in violation for violation in rule_result["violations"]):
                result["severity_level"] = "CRITICAL"
                result["severity_score"] = float(max(result["severity_score"], 8.0))
            elif result["severity_level"] == "NORMAL":
                result["severity_level"] = "MEDIUM"
                result["severity_score"] = float(max(result["severity_score"], 4.0))
        
        result["details"]["model_status"] = "Model loaded and functional"
        
        # Ensure all numeric values are JSON serializable Python types
        result["anomaly_score"] = float(result["anomaly_score"])
        result["severity_score"] = float(result["severity_score"])
        result["confidence"] = float(result["confidence"])
        result["is_anomaly"] = bool(result["is_anomaly"])
        
    except Exception as e:
        logger.error(f"Error in model-based anomaly detection: {e}")
        result["details"]["model_error"] = str(e)
        return rule_based_detection_only(sensor_data, device_id, result)
    
    return result

def rule_based_detection_only(sensor_data: Dict, device_id: str, result: Dict) -> Dict:
    """
    Fallback to rule-based detection when model is not available
    """
    rule_result = check_vital_thresholds(sensor_data)
    if rule_result["violations"]:
        result["is_anomaly"] = True
        result["anomaly_type"] = rule_result["violations"]
        result["details"]["rule_violations"] = rule_result["details"]
        
        # Determine severity
        if any("Critical" in violation for violation in rule_result["violations"]):
            result["severity_level"] = "CRITICAL"
            result["severity_score"] = 8.0
        else:
            result["severity_level"] = "MEDIUM"
            result["severity_score"] = 4.0
    
    # Ensure all numeric values are Python types
    result["anomaly_score"] = float(result["anomaly_score"])
    result["severity_score"] = float(result["severity_score"])
    result["confidence"] = float(result["confidence"])
    
    return result

def check_vital_thresholds(data: Dict) -> Dict:
    """
    Rule-based anomaly detection using predefined thresholds
    """
    violations = []
    details = {}
    
    # Vital sign thresholds
    vital_thresholds = {
        'heart_rate': {'low': 60, 'high': 100, 'critical_low': 40, 'critical_high': 120},
        'systolic_bp': {'low': 90, 'high': 140, 'critical_low': 70, 'critical_high': 180},
        'diastolic_bp': {'low': 60, 'high': 90, 'critical_low': 40, 'critical_high': 110},
        'temperature': {'low': 36.1, 'high': 37.2, 'critical_low': 35.0, 'critical_high': 39.0},
        'oxygen_level': {'low': 95, 'high': 100, 'critical_low': 90, 'critical_high': 100},
        'respiratory_rate': {'low': 12, 'high': 20, 'critical_low': 8, 'critical_high': 30},
        'glucose': {'low': 70, 'high': 140, 'critical_low': 50, 'critical_high': 200}
    }
    
    # Environment thresholds
    environment_thresholds = {
        'room_temperature': {'low': 20, 'high': 24, 'critical_low': 15, 'critical_high': 30},
        'humidity': {'low': 40, 'high': 60, 'critical_low': 20, 'critical_high': 80},
        'air_quality': {'low': 0, 'high': 50, 'critical_low': 0, 'critical_high': 100}
    }
    
    # Check vital signs
    for vital, value in data.items():
        if vital in vital_thresholds:
            thresholds = vital_thresholds[vital]
            
            if value < thresholds['critical_low']:
                violations.append(f"Critical Low {vital.replace('_', ' ').title()}")
                details[vital] = f"Value {value} below critical threshold {thresholds['critical_low']}"
            elif value > thresholds['critical_high']:
                violations.append(f"Critical High {vital.replace('_', ' ').title()}")
                details[vital] = f"Value {value} above critical threshold {thresholds['critical_high']}"
            elif value < thresholds['low']:
                violations.append(f"Low {vital.replace('_', ' ').title()}")
                details[vital] = f"Value {value} below normal threshold {thresholds['low']}"
            elif value > thresholds['high']:
                violations.append(f"High {vital.replace('_', ' ').title()}")
                details[vital] = f"Value {value} above normal threshold {thresholds['high']}"
    
    # Check environment
    for param, value in data.items():
        if param in environment_thresholds:
            thresholds = environment_thresholds[param]
            
            if value < thresholds['critical_low'] or value > thresholds['critical_high']:
                violations.append(f"Critical Environment: {param.replace('_', ' ').title()}")
                details[param] = f"Value {value} outside critical range [{thresholds['critical_low']}, {thresholds['critical_high']}]"
            elif value < thresholds['low'] or value > thresholds['high']:
                violations.append(f"Environment Alert: {param.replace('_', ' ').title()}")
                details[param] = f"Value {value} outside normal range [{thresholds['low']}, {thresholds['high']}]"
    
    return {"violations": violations, "details": details}

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
        vitals_ref = get_ref(f"iotData/{device_id}/vitals")
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
        
        # Sanitize timestamp for Firebase
        safe_timestamp = timestamp.replace(':', '-').replace('.', '-')
        
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
    
    if not anomaly_types:
        return f"Anomaly detected for device {device_id}"
    
    if len(anomaly_types) == 1:
        return f"{severity} Alert: {anomaly_types[0]} detected for device {device_id}"
    else:
        return f"{severity} Alert: Multiple anomalies detected for device {device_id}: {', '.join(anomaly_types)}"

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
async def detect_anomaly(monitor_id: str, background_tasks: BackgroundTasks):
    """
    Detect anomalies for a specific monitor by getting its latest vitals
    """
    try:
        # Get latest vitals for the monitor
        vitals_ref = get_ref(f"iotData/{monitor_id}/vitals")
        vitals_data = vitals_ref.get() or {}
        
        if not vitals_data:
            raise HTTPException(status_code=404, detail=f"No vitals data found for monitor {monitor_id}")
        
        # Get the most recent reading
        latest_timestamp = sorted(vitals_data.keys())[-1]
        latest_vitals = vitals_data[latest_timestamp]
        
        # Perform anomaly detection
        anomaly_result = detect_anomaly_with_model(
            sensor_data=latest_vitals,
            device_id=monitor_id
        )
        
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
                    # Include data if timestamp parsing fails
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
