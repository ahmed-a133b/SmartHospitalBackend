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

# @router.get("/{device_id}/vitals")
# def get_device_vitals(device_id: str):
#     """Return all vitals readings for current patient only."""
#     device_data = get_ref(f"iotData/{device_id}").get()
#     if not device_data:
#         return {}
    
#     current_patient_id = device_data.get("deviceInfo", {}).get("currentPatientId")
#     if not current_patient_id:
#         return {}
    
#     # Return vitals for current patient only
#     vitals = get_ref(f"iotData/{device_id}/vitals").get() or {}
#     return vitals.get(current_patient_id, {})

@router.get("/{device_id}/vitals/latest")
def get_latest_vitals(device_id: str):
    """Return the most recent vitals reading for current patient."""
    device_data = get_ref(f"iotData/{device_id}").get()
    if not device_data:
        return {}
    
    current_patient_id = device_data.get("deviceInfo", {}).get("currentPatientId")
    if not current_patient_id:
        return {}
    
    # Get vitals for current patient
    vitals = get_ref(f"iotData/{device_id}/vitals/{current_patient_id}").get()
    if not vitals:
        return {}

    latest_ts = sorted(vitals.keys())[-1]
    return {"timestamp": latest_ts, "data": vitals[latest_ts], "patientId": current_patient_id}

@router.get("/{device_id}/vitals/patient/{patient_id}")
def get_patient_vitals(device_id: str, patient_id: str):
    """Return all vitals readings for a specific patient on a device."""
    device_data = get_ref(f"iotData/{device_id}").get()
    if not device_data:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Verify patient is currently assigned to this device
    current_patient_id = device_data.get("deviceInfo", {}).get("currentPatientId")
    if current_patient_id != patient_id:
        raise HTTPException(status_code=403, detail="Patient is not currently assigned to this device")
    
    return get_ref(f"iotData/{device_id}/vitals/{patient_id}").get() or {}

@router.post("/{device_id}/vitals")
def post_vitals(device_id: str, data: dict):
    """Post new vitals data for the currently assigned patient only"""
    try:
        # Get device data to check current patient assignment
        device_data = get_ref(f"iotData/{device_id}").get()
        if not device_data:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Get currently assigned patient
        current_patient_id = device_data.get("deviceInfo", {}).get("currentPatientId")
        if not current_patient_id:
            raise HTTPException(status_code=400, detail="No patient assigned to this monitor. Cannot store vitals.")
        
        # Generate timestamp
        timestamp = datetime.now().isoformat()
        timestamp = sanitize_timestamp(timestamp)
        
        # Store vitals under current patient ID only
        # Structure: vitals[patient_id][timestamp] = vital_record
        vitals_ref = get_ref(f"iotData/{device_id}/vitals/{current_patient_id}/{timestamp}")
        vitals_ref.set(data)
        
        return {
            "message": f"Vitals saved for device {device_id}, patient {current_patient_id}",
            "timestamp": timestamp,
            "patientId": current_patient_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error posting vitals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

@router.post("/{device_id}/assign-patient")
def assign_patient_to_monitor(device_id: str, data: dict):
    """Assign a patient to a monitor device"""
    try:
        patient_id = data.get("patientId")
        if not patient_id:
            raise HTTPException(status_code=400, detail="Patient ID is required")
        
        # Get device data
        device_ref = get_ref(f"iotData/{device_id}")
        device_data = device_ref.get()
        
        if not device_data:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Check if device is a vitals monitor
        if device_data.get("deviceInfo", {}).get("type") != "vitals_monitor":
            raise HTTPException(status_code=400, detail="Only vitals monitors can be assigned to patients")
        
        # Check if patient exists
        patient_ref = get_ref(f"patients/{patient_id}")
        patient_data = patient_ref.get()
        
        if not patient_data:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get device room and bed info
        device_info = device_data.get("deviceInfo", {})
        device_room_id = device_info.get("roomId")
        device_bed_id = device_info.get("bedId")
        
        # Verify patient is in the same room/bed if device is assigned to a bed
        patient_room_id = patient_data.get("personalInfo", {}).get("roomId")
        patient_bed_id = patient_data.get("personalInfo", {}).get("bedId")
        
        if device_bed_id and patient_bed_id != device_bed_id:
            raise HTTPException(
                status_code=400, 
                detail=f"Patient is not assigned to the bed {device_bed_id} that this monitor is assigned to"
            )
        
        if device_room_id and patient_room_id != device_room_id:
            raise HTTPException(
                status_code=400, 
                detail=f"Patient is not in the same room {device_room_id} as the monitor"
            )
        
        # Unassign patient from any other monitors
        iot_ref = get_ref("iotData")
        all_devices = iot_ref.get() or {}
        
        for other_device_id, other_device_data in all_devices.items():
            if (other_device_id != device_id and 
                other_device_data.get("deviceInfo", {}).get("currentPatientId") == patient_id):
                # Remove patient from other device
                other_device_data["deviceInfo"]["currentPatientId"] = None
                get_ref(f"iotData/{other_device_id}").set(other_device_data)
                logger.info(f"Removed patient {patient_id} from device {other_device_id}")
        
        # Assign patient to this monitor
        device_data["deviceInfo"]["currentPatientId"] = patient_id
        
        # Clear all previous vitals since we only store current patient's vitals
        # New structure: vitals[patient_id][timestamp] = vital_record
        device_data["vitals"] = {}
        
        # Save device data
        device_ref.set(device_data)
        
        logger.info(f"Patient {patient_id} assigned to monitor {device_id}")
        return {"message": f"Patient {patient_id} assigned to monitor {device_id} successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning patient to monitor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{device_id}/unassign-patient")
def unassign_patient_from_monitor(device_id: str):
    """Unassign/detach patient from a monitor device"""
    try:
        # Get device data
        device_ref = get_ref(f"iotData/{device_id}")
        device_data = device_ref.get()
        
        if not device_data:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Check if device has a patient assigned
        current_patient_id = device_data.get("deviceInfo", {}).get("currentPatientId")
        
        if not current_patient_id:
            raise HTTPException(status_code=400, detail="No patient is currently assigned to this monitor")
        
        # Remove patient assignment
        device_data["deviceInfo"]["currentPatientId"] = None
        
        # Clear all vitals since we don't store historical vitals
        device_data["vitals"] = {}
        
        # Save device data
        device_ref.set(device_data)
        
        logger.info(f"Patient {current_patient_id} unassigned from monitor {device_id}")
        return {"message": f"Patient {current_patient_id} unassigned from monitor {device_id} successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unassigning patient from monitor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{device_id}/available-patients")
def get_available_patients_for_monitor(device_id: str):
    """Get available patients in the same room as the monitor for assignment"""
    try:
        # Get device data
        device_ref = get_ref(f"iotData/{device_id}")
        device_data = device_ref.get()
        
        if not device_data:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device_info = device_data.get("deviceInfo", {})
        device_room_id = device_info.get("roomId")
        device_bed_id = device_info.get("bedId")
        
        if not device_room_id:
            return {"availablePatients": []}
        
        # Get all patients
        patients_ref = get_ref("patients")
        all_patients = patients_ref.get() or {}
        
        # Filter patients by room and bed availability
        available_patients = []
        
        for patient_id, patient_data in all_patients.items():
            personal_info = patient_data.get("personalInfo", {})
            patient_room_id = personal_info.get("roomId")
            patient_bed_id = personal_info.get("bedId")
            
            # Patient must be in the same room
            if patient_room_id != device_room_id:
                continue
            
            # If monitor is assigned to a specific bed, patient must be in that bed
            if device_bed_id and patient_bed_id != device_bed_id:
                continue
            
            # Check if patient is already assigned to another monitor
            patient_has_monitor = False
            iot_ref = get_ref("iotData")
            all_devices = iot_ref.get() or {}
            
            for other_device_data in all_devices.values():
                if (other_device_data.get("deviceInfo", {}).get("currentPatientId") == patient_id and
                    other_device_data.get("deviceInfo", {}).get("type") == "vitals_monitor"):
                    patient_has_monitor = True
                    break
            
            if not patient_has_monitor:
                available_patients.append({
                    "patientId": patient_id,
                    "name": personal_info.get("name", "Unknown"),
                    "roomId": patient_room_id,
                    "bedId": patient_bed_id
                })
        
        return {"availablePatients": available_patients}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting available patients: {e}")
        raise HTTPException(status_code=500, detail=str(e))