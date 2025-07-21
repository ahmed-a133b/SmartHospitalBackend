# app/routers/iot.py
from fastapi import APIRouter, BackgroundTasks
from app.firebase_config import get_ref
from datetime import datetime
import re
import logging

router = APIRouter(prefix="/iotData", tags=["IoT Sensor Data"])
logger = logging.getLogger(__name__)



def sanitize_timestamp(timestamp):
        # Convert ISO timestamp to a Firebase-safe string
        # Replace colons, periods, and other invalid characters
        sanitized = re.sub(r'[.:]', '-', timestamp)
        # Remove any other invalid characters for Firebase paths
        sanitized = re.sub(r'[#\$\[\]]', '', sanitized)
        return sanitized

@router.get("/")
def get_all_devices():
    """Return all IoT devices and their vitals."""
    data = get_ref("iotData").get()
    return data or {}

@router.get("/{device_id}")
def get_device_data(device_id: str):
    """Return all sensor data for a specific device."""
    return get_ref(f"iotData/{device_id}").get() or {}

@router.get("/{device_id}/vitals")
def get_device_vitals(device_id: str):
    """Return all vitals readings (timestamped) for a device."""
    return get_ref(f"iotData/{device_id}/vitals").get() or {}

@router.get("/{device_id}/vitals/latest")
def get_latest_vitals(device_id: str):
    """Return the most recent vitals reading for a device."""
    vitals = get_ref(f"iotData/{device_id}/vitals").get()
    if not vitals:
        return {}

    latest_ts = sorted(vitals.keys())[-1]
    return {"timestamp": latest_ts, "data": vitals[latest_ts]}

@router.post("/{device_id}/vitals")
def post_vitals(device_id: str, data: dict, background_tasks: BackgroundTasks):
    """Post new vitals data and trigger anomaly detection"""
    from app.anomaly_detection import anomaly_engine
    
    timestamp = datetime.now().isoformat()
    timestamp = sanitize_timestamp(timestamp)
    ref = get_ref(f"iotData/{device_id}/vitals/{timestamp}")
    ref.set(data)
    
    # Trigger anomaly detection in background
    def detect_and_save_anomaly():
        try:
            # Get recent vitals for trend analysis
            vitals_ref = get_ref(f"iotData/{device_id}/vitals")
            recent_vitals_data = vitals_ref.get() or {}
            
            # Get last 10 readings for trend analysis
            recent_readings = []
            sorted_timestamps = sorted(recent_vitals_data.keys())[-10:]
            for ts in sorted_timestamps:
                recent_readings.append(recent_vitals_data[ts])
            
            # Perform anomaly detection
            anomaly_result = anomaly_engine.detect_anomaly(
                sensor_data=data,
                device_id=device_id,
                recent_data=recent_readings
            )
            
            # Save anomaly log
            safe_timestamp = anomaly_result["timestamp"].replace(':', '-').replace('.', '-')
            anomaly_ref = get_ref(f"anomalies/{device_id}/{safe_timestamp}")
            anomaly_ref.set(anomaly_result)
            
            # If anomaly detected, create alert
            if anomaly_result["is_anomaly"]:
                alert_data = {
                    "device_id": device_id,
                    "timestamp": anomaly_result["timestamp"],
                    "severity_level": anomaly_result["severity_level"],
                    "severity_score": anomaly_result["severity_score"],
                    "anomaly_type": anomaly_result["anomaly_type"],
                    "message": f"{anomaly_result['severity_level']} Alert: {', '.join(anomaly_result['anomaly_type'])} detected for device {device_id}",
                    "resolved": False,
                    "details": anomaly_result.get("details", {}),
                    "trend_analysis": anomaly_result.get("trend_analysis", {})
                }
                
                alert_ref = get_ref(f"iotData/{device_id}/alerts/{safe_timestamp}")
                alert_ref.set(alert_data)
                
                logger.info(f"Anomaly alert created for device {device_id}: {alert_data['severity_level']}")
                
        except Exception as e:
            logger.error(f"Error in background anomaly detection: {e}")
    
    background_tasks.add_task(detect_and_save_anomaly)
    
    return {
        "message": f"Vitals saved for device {device_id}",
        "timestamp": timestamp
    }