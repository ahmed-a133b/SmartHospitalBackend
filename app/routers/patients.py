from fastapi import APIRouter, HTTPException
from typing import Optional
import logging
from app.firebase_config import get_ref

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("/")
async def get_all_patients(
    ward: Optional[str] = None,
    status: Optional[str] = None,
    risk_level: Optional[str] = None
):
    """
    Get all patients with optional filtering
    - ward: Filter by ward (e.g., 'Cardiology')
    - status: Filter by current status (stable, critical, improving, deteriorating)
    - risk_level: Filter by risk level (Low, Moderate, High, Critical)
    """
    try:
        ref = get_ref("patients")
        patients = ref.get() or {}
        
        # Apply filters if provided
        if ward or status or risk_level:
            filtered_patients = {}
            for patient_id, patient in patients.items():
                if ward and patient.get("personalInfo", {}).get("ward") != ward:
                    continue
                if status and patient.get("currentStatus", {}).get("status") != status:
                    continue
                if risk_level and patient.get("predictions", {}).get("riskLevel") != risk_level:
                    continue
                filtered_patients[patient_id] = patient
            return filtered_patients
        
        return patients
    except Exception as e:
        logger.error(f"Error fetching patients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{patient_id}")
async def get_patient(patient_id: str):
    """Get a specific patient's complete record"""
    try:
        ref = get_ref(f"patients/{patient_id}")
        patient = ref.get()
        
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
            
        return patient
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_patient(patient: dict):
    """Create a new patient record (no validation)"""
    try:
        ref = get_ref("patients")
        new_patient_ref = ref.push(patient)
        return {
            "message": "Patient created successfully",
            "patient_id": new_patient_ref.key
        }
    except Exception as e:
        logger.error(f"Error creating patient: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{patient_id}")
async def update_patient(
    patient_id: str,
    patient: dict
):
    """Update a patient's complete record (no validation)"""
    try:
        ref = get_ref(f"patients/{patient_id}")
        if not ref.get():
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
        ref.set(patient)
        return {"message": f"Patient {patient_id} updated successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{patient_id}")
async def partial_update_patient(
    patient_id: str,
    update: dict
):
    """Partially update a patient's record (no validation)"""
    try:
        ref = get_ref(f"patients/{patient_id}")
        current_data = ref.get()
        if not current_data:
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
        update_data = {k: v for k, v in update.items() if v is not None}
        ref.update(update_data)
        return {"message": f"Patient {patient_id} updated successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{patient_id}")
async def delete_patient(patient_id: str):
    """Delete a patient record"""
    try:
        ref = get_ref(f"patients/{patient_id}")
        if not ref.get():
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
            
        ref.delete()
        return {"message": f"Patient {patient_id} deleted successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{patient_id}/vitals")
async def get_patient_vitals(
    patient_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: Optional[int] = 10
):
    """Get patient's vital signs history"""
    try:
        # First verify patient exists
        patient_ref = get_ref(f"patients/{patient_id}")
        if not patient_ref.get():
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
        
        # Get IoT data for the patient
        iot_ref = get_ref("iotData")
        monitors = iot_ref.get() or {}
        
        vitals_history = []
        for monitor in monitors.values():
            if "vitals" not in monitor:
                continue
                
            for timestamp, vitals in monitor["vitals"].items():
                if vitals.get("patientId") != patient_id:
                    continue
                    
                # Apply time filter if provided
                if start_time and timestamp < start_time:
                    continue
                if end_time and timestamp > end_time:
                    continue
                    
                vitals["timestamp"] = timestamp
                vitals_history.append(vitals)
        
        # Sort by timestamp and limit results
        vitals_history.sort(key=lambda x: x["timestamp"], reverse=True)
        return vitals_history[:limit]
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching vitals for patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{patient_id}/treatments")
async def get_patient_treatments(
    patient_id: str,
    status: Optional[str] = None
):
    """Get patient's treatment history"""
    try:
        ref = get_ref(f"patients/{patient_id}")
        patient = ref.get()
        
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
            
        treatments = patient.get("treatments", [])
        
        # Apply status filter if provided
        if status:
            treatments = [t for t in treatments if t.get("status") == status]
            
        return treatments
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching treatments for patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ward/{ward_id}")
async def get_ward_patients(
    ward_id: str,
    status: Optional[str] = None
):
    """Get all patients in a specific ward"""
    try:
        ref = get_ref("patients")
        all_patients = ref.get() or {}
        
        # Filter patients by ward
        ward_patients = {}
        for patient_id, patient in all_patients.items():
            if patient.get("personalInfo", {}).get("ward") == ward_id:
                if status and patient.get("currentStatus", {}).get("status") != status:
                    continue
                ward_patients[patient_id] = patient
                
        return ward_patients
    except Exception as e:
        logger.error(f"Error fetching patients for ward {ward_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk/{risk_level}")
async def get_patients_by_risk(
    risk_level: str,
    ward: Optional[str] = None
):
    """Get all patients with a specific risk level"""
    try:
        ref = get_ref("patients")
        all_patients = ref.get() or {}
        
        # Filter patients by risk level
        risk_patients = {}
        for patient_id, patient in all_patients.items():
            if patient.get("predictions", {}).get("riskLevel") == risk_level:
                if ward and patient.get("personalInfo", {}).get("ward") != ward:
                    continue
                risk_patients[patient_id] = patient
                
        return risk_patients
    except Exception as e:
        logger.error(f"Error fetching patients with risk level {risk_level}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

