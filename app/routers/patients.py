from fastapi import APIRouter
from firebase_config import get_ref

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("/")
def get_all_patients():
    ref = get_ref("patients")
    return ref.get() or {}

@router.get("/{patient_id}")
def get_patient(patient_id: str):
    ref = get_ref(f"patients/{patient_id}")
    return ref.get() or {}
