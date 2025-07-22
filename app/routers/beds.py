from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.firebase_config import get_ref
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/beds", tags=["beds"])

class BedData(BaseModel):
    roomId: str
    bedNumber: str
    type: str  # 'ICU', 'isolation', 'standard', 'surgery'
    status: str  # 'occupied', 'available', 'maintenance', 'cleaning'
    patientId: Optional[str] = None
    features: List[str] = []
    lastCleaned: Optional[str] = None
    position: Optional[Dict[str, Any]] = None

@router.get("/")
async def get_all_beds():
    """Get all beds"""
    try:
        ref = get_ref("beds")
        beds = ref.get() or {}
        return beds
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch beds: {str(e)}")

@router.get("/{bed_id}")
async def get_bed(bed_id: str):
    """Get a specific bed by ID"""
    try:
        ref = get_ref(f"beds/{bed_id}")
        bed = ref.get()
        
        if not bed:
            raise HTTPException(status_code=404, detail="Bed not found")
            
        return bed
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch bed: {str(e)}")

@router.get("/room/{room_id}")
async def get_room_beds(room_id: str):
    """Get all beds in a specific room"""
    try:
        ref = get_ref("beds")
        all_beds = ref.get() or {}
        
        room_beds = {bed_id: bed_data for bed_id, bed_data in all_beds.items() 
                    if bed_data.get('roomId') == room_id}
        
        return room_beds
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch room beds: {str(e)}")

@router.get("/room/{room_id}/available")
async def get_available_beds_in_room(room_id: str):
    """Get all available beds in a specific room"""
    try:
        ref = get_ref("beds")
        all_beds = ref.get() or {}
        
        available_beds = {bed_id: bed_data for bed_id, bed_data in all_beds.items() 
                         if (bed_data.get('roomId') == room_id and 
                             bed_data.get('status') == 'available')}
        
        return available_beds
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch available beds: {str(e)}")

@router.post("/{bed_id}/assign-patient/{patient_id}")
async def assign_patient_to_bed(bed_id: str, patient_id: str):
    """Assign a patient to a specific bed"""
    try:
        # Check if bed exists and is available
        bed_ref = get_ref(f"beds/{bed_id}")
        bed_data = bed_ref.get()
        
        if not bed_data:
            raise HTTPException(status_code=404, detail="Bed not found")
            
        if bed_data.get('status') != 'available':
            raise HTTPException(status_code=400, detail="Bed is not available")
            
        # Check if patient exists
        patient_ref = get_ref(f"patients/{patient_id}")
        patient_data = patient_ref.get()
        
        if not patient_data:
            raise HTTPException(status_code=404, detail="Patient not found")
            
        # Check if patient is already assigned to another bed
        current_bed_id = patient_data.get('personalInfo', {}).get('bedId')
        if current_bed_id and current_bed_id != bed_id:
            # Discharge from current bed first
            await discharge_patient_from_bed(current_bed_id, patient_id)
        
        # Assign patient to bed
        bed_data['patientId'] = patient_id
        bed_data['status'] = 'occupied'
        bed_ref.set(bed_data)
        
        # Update patient's bed assignment
        patient_data['personalInfo']['bedId'] = bed_id
        patient_data['personalInfo']['roomId'] = bed_data['roomId']
        patient_ref.set(patient_data)
        
        # Update room status to occupied if it wasn't already
        room_ref = get_ref(f"rooms/{bed_data['roomId']}")
        room_data = room_ref.get()
        if room_data and room_data.get('status') != 'occupied':
            room_ref.update({'status': 'occupied'})
        
        logger.info(f"Patient {patient_id} assigned to bed {bed_id} in room {bed_data['roomId']}")
        return {"message": f"Patient {patient_id} assigned to bed {bed_id} successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning patient to bed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to assign patient to bed: {str(e)}")

@router.delete("/{bed_id}/discharge-patient/{patient_id}")
async def discharge_patient_from_bed(bed_id: str, patient_id: str):
    """Discharge a patient from a specific bed"""
    try:
        # Check if bed exists
        bed_ref = get_ref(f"beds/{bed_id}")
        bed_data = bed_ref.get()
        
        if not bed_data:
            raise HTTPException(status_code=404, detail="Bed not found")
            
        # Check if patient is actually assigned to this bed
        if bed_data.get('patientId') != patient_id:
            raise HTTPException(status_code=400, detail="Patient is not assigned to this bed")
            
        # Update bed status
        bed_data['patientId'] = None
        bed_data['status'] = 'available'
        bed_ref.set(bed_data)
        
        # Update patient record
        patient_ref = get_ref(f"patients/{patient_id}")
        patient_data = patient_ref.get()
        
        if patient_data:
            patient_data['personalInfo']['bedId'] = None
            patient_data['personalInfo']['roomId'] = None
            patient_ref.set(patient_data)
        
        # Check if room should be marked as available
        room_id = bed_data['roomId']
        await update_room_status_based_on_beds(room_id)
        
        logger.info(f"Patient {patient_id} discharged from bed {bed_id}")
        return {"message": f"Patient {patient_id} discharged from bed {bed_id} successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error discharging patient from bed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to discharge patient from bed: {str(e)}")

@router.get("/patient/{patient_id}")
async def get_patient_bed(patient_id: str):
    """Get the bed assigned to a specific patient"""
    try:
        # Get patient data
        patient_ref = get_ref(f"patients/{patient_id}")
        patient_data = patient_ref.get()
        
        if not patient_data:
            raise HTTPException(status_code=404, detail="Patient not found")
            
        bed_id = patient_data.get('personalInfo', {}).get('bedId')
        if not bed_id:
            return {"message": "Patient is not assigned to any bed", "bed": None}
            
        # Get bed data
        bed_ref = get_ref(f"beds/{bed_id}")
        bed_data = bed_ref.get()
        
        return {"bed_id": bed_id, "bed_data": bed_data}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patient bed: {str(e)}")

# Helper functions
async def update_room_status_based_on_beds(room_id: str):
    """Update room status based on bed occupancy"""
    try:
        # Get all beds in the room
        beds_ref = get_ref("beds")
        all_beds = beds_ref.get() or {}
        
        room_beds = [bed for bed in all_beds.values() if bed.get('roomId') == room_id]
        
        # Check if any beds are occupied
        occupied_beds = [bed for bed in room_beds if bed.get('status') == 'occupied']
        
        # Update room status
        room_ref = get_ref(f"rooms/{room_id}")
        room_data = room_ref.get()
        
        if room_data:
            new_status = 'occupied' if occupied_beds else 'available'
            if room_data.get('status') != new_status:
                room_ref.update({'status': new_status})
                
    except Exception as e:
        logger.error(f"Error updating room status: {str(e)}")

async def find_available_bed_in_room(room_id: str, bed_type: Optional[str] = None) -> Optional[str]:
    """Find an available bed in a room, optionally filtered by type"""
    try:
        beds_ref = get_ref("beds")
        all_beds = beds_ref.get() or {}
        
        for bed_id, bed_data in all_beds.items():
            if (bed_data.get('roomId') == room_id and 
                bed_data.get('status') == 'available' and
                (bed_type is None or bed_data.get('type') == bed_type)):
                return bed_id
                
        return None
        
    except Exception as e:
        logger.error(f"Error finding available bed: {str(e)}")
        return None

@router.get("/stats/occupancy")
async def get_bed_occupancy_stats():
    """Get bed occupancy statistics"""
    try:
        beds_ref = get_ref("beds")
        all_beds = beds_ref.get() or {}
        
        stats = {
            'total': len(all_beds),
            'occupied': 0,
            'available': 0,
            'maintenance': 0,
            'cleaning': 0,
            'by_type': {},
            'by_room': {}
        }
        
        for bed_id, bed_data in all_beds.items():
            status = bed_data.get('status', 'available')
            bed_type = bed_data.get('type', 'standard')
            room_id = bed_data.get('roomId', 'unknown')
            
            # Count by status
            if status in stats:
                stats[status] += 1
                
            # Count by type
            if bed_type not in stats['by_type']:
                stats['by_type'][bed_type] = {'total': 0, 'occupied': 0, 'available': 0}
            stats['by_type'][bed_type]['total'] += 1
            stats['by_type'][bed_type][status] = stats['by_type'][bed_type].get(status, 0) + 1
            
            # Count by room
            if room_id not in stats['by_room']:
                stats['by_room'][room_id] = {'total': 0, 'occupied': 0, 'available': 0}
            stats['by_room'][room_id]['total'] += 1
            stats['by_room'][room_id][status] = stats['by_room'][room_id].get(status, 0) + 1
        
        stats['occupancy_rate'] = (stats['occupied'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get bed occupancy stats: {str(e)}")
