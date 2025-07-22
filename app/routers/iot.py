# app/routers/iot.py
from fastapi import APIRouter, HTTPException
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
def post_vitals(device_id: str, data: dict):
    """Post new vitals data"""
    timestamp = datetime.now().isoformat()
    timestamp = sanitize_timestamp(timestamp)
    ref = get_ref(f"iotData/{device_id}/vitals/{timestamp}")
    ref.set(data)
    
    return {
        "message": f"Vitals saved for device {device_id}",
        "timestamp": timestamp
    }

@router.put("/{device_id}/deviceInfo")
def update_device_info(device_id: str, device_info: dict):
    """Update device information including room assignment"""
    try:
        # Get existing device data
        device_data = get_ref(f"iotData/{device_id}").get()
        if not device_data:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Update device info
        device_data["deviceInfo"] = {**device_data.get("deviceInfo", {}), **device_info}
        
        # Save back to Firebase
        get_ref(f"iotData/{device_id}").set(device_data)
        
        logger.info(f"Device {device_id} info updated")
        return {"message": "Device info updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating device info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{device_id}/alerts/{alert_id}/resolve")
def resolve_alert(device_id: str, alert_id: str, data: dict):
    """Resolve an alert for a device"""
    try:
        alert_ref = get_ref(f"iotData/{device_id}/alerts/{alert_id}")
        alert_data = alert_ref.get()
        
        if not alert_data:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Update alert with resolution data
        alert_data["resolved"] = True
        alert_data["resolvedBy"] = data.get("resolvedBy")
        alert_data["resolvedAt"] = data.get("resolvedAt")
        
        # Save back to Firebase
        alert_ref.set(alert_data)
        
        logger.info(f"Alert {alert_id} resolved for device {device_id}")
        return {"message": "Alert resolved successfully"}
        
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{device_id}/alerts/{alert_id}/assign")
def assign_alert(device_id: str, alert_id: str, data: dict):
    """Assign an alert to a staff member"""
    try:
        alert_ref = get_ref(f"iotData/{device_id}/alerts/{alert_id}")
        alert_data = alert_ref.get()
        
        if not alert_data:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Update alert with assignment data
        alert_data["assignedTo"] = data.get("assignedTo")
        
        # Save back to Firebase
        alert_ref.set(alert_data)
        
        logger.info(f"Alert {alert_id} assigned to {data.get('assignedTo')} for device {device_id}")
        return {"message": "Alert assigned successfully"}
        
    except Exception as e:
        logger.error(f"Error assigning alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))