# app/routers/iot.py
from fastapi import APIRouter
from app.firebase_config import get_ref

router = APIRouter(prefix="/iotData", tags=["IoT Sensor Data"])

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
