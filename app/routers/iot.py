# app/routers/iot.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.firebase_config import get_ref
from datetime import datetime
router = APIRouter(prefix="/iotData", tags=["IoT Sensor Data"])

class VitalsData(BaseModel):
    heartRate: float
    oxygenLevel: float
    temperature: float
    bloodPressure: dict
    respiratoryRate: float
    glucose: float
    bedOccupancy: bool = False
    patientId: str
    deviceStatus: str = "online"
    batteryLevel: float = 100.0
    signalStrength: float = 100.0

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
def post_vitals(device_id: str, data: VitalsData):
    timestamp = datetime.utcnow().isoformat()
    ref = get_ref(f"iotData/{device_id}/vitals/{timestamp}")
    ref.set(data.dict())
    return {
        "message": f"Vitals saved for device {device_id}",
        "timestamp": timestamp
    }