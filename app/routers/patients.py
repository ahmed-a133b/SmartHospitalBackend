from fastapi import APIRouter
from app.firebase_config import get_ref
from pydantic import BaseModel
router = APIRouter(prefix="/patients", tags=["Patients"])

class PatientRecord(BaseModel):
    personalInfo: dict
    medicalHistory: dict = {}
    currentStatus: dict = {}
    predictions: dict = {}

@router.get("/")
def get_all_patients():
    ref = get_ref("patients")
    return ref.get() or {}

@router.get("/{patient_id}")
def get_patient(patient_id: str):
    ref = get_ref(f"patients/{patient_id}")
    return ref.get() or {}

@router.post("/{patient_id}")
def add_or_update_patient(patient_id: str, record: PatientRecord):
    ref = get_ref(f"patients/{patient_id}")
    ref.set(record.model_dump())  # Overwrites or creates new
    return {"message": f"Patient {patient_id} saved successfully"}

