from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
from datetime import datetime, date
from app.firebase_config import get_ref
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/staff", tags=["Staff"])



@router.get("/{staff_id}")
async def get_staff(staff_id: str):
    """Get staff member details by ID"""
    try:
        staff_ref = get_ref(f'staff/{staff_id}')
        staff_data = staff_ref.get()
        
        if not staff_data:
            raise HTTPException(status_code=404, detail=f"Staff member {staff_id} not found")
            
        return staff_data
    except Exception as e:
        logger.error(f"Error fetching staff data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_staff(
    role: Optional[str] = None,
    department: Optional[str] = None,
    onDuty: Optional[bool] = None
):
    """List all staff members with optional filters"""
    try:
        staff_ref = get_ref('staff')
        staff_data = staff_ref.get()
        
        if not staff_data:
            return []
            
        # Apply filters if provided
        filtered_staff = {}
        for staff_id, staff in staff_data.items():
            if role and staff.get('personalInfo', {}).get('role') != role:
                continue
            if department and staff.get('personalInfo', {}).get('department') != department:
                continue
            if onDuty is not None and staff.get('currentStatus', {}).get('onDuty') != onDuty:
                continue
            filtered_staff[staff_id] = staff
            
        return filtered_staff
    except Exception as e:
        logger.error(f"Error listing staff: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_staff(staff: dict):
    """Create a new staff member (no validation)"""
    try:
        staff_ref = get_ref('staff')
        new_staff_ref = staff_ref.push(staff)
        return {"id": new_staff_ref.key, "data": staff}
    except Exception as e:
        logger.error(f"Error creating staff: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{staff_id}")
async def update_staff(staff_id: str, staff: dict):
    """Update staff member details (no validation)"""
    try:
        staff_ref = get_ref(f'staff/{staff_id}')
        current_data = staff_ref.get()
        if not current_data:
            raise HTTPException(status_code=404, detail=f"Staff member {staff_id} not found")
        update_data = {k: v for k, v in staff.items() if v is not None}
        staff_ref.update(update_data)
        return {"message": "Staff updated successfully"}
    except Exception as e:
        logger.error(f"Error updating staff: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{staff_id}")
async def delete_staff(staff_id: str):
    """Delete a staff member"""
    try:
        staff_ref = get_ref(f'staff/{staff_id}')
        if not staff_ref.get():
            raise HTTPException(status_code=404, detail=f"Staff member {staff_id} not found")
            
        staff_ref.delete()
        return {"message": "Staff deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting staff: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{staff_id}/schedule")
async def get_staff_schedule(
    staff_id: str,
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format")
):
    """Get staff schedule for a date range"""
    try:
        staff_ref = get_ref(f'staff/{staff_id}')
        staff_data = staff_ref.get()
        
        if not staff_data:
            raise HTTPException(status_code=404, detail=f"Staff member {staff_id} not found")
            
        schedule = staff_data.get('schedule', {})
        
        # Filter schedule by date range
        filtered_schedule = {}
        for date_str, shift in schedule.items():
            if date_str >= start_date and (not end_date or date_str <= end_date):
                filtered_schedule[date_str] = shift
                
        return filtered_schedule
    except Exception as e:
        logger.error(f"Error fetching staff schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{staff_id}/schedule/{date}")
async def update_staff_schedule(staff_id: str, date: str, shift: dict):
    """Update staff schedule for a specific date (no validation)"""
    try:
        staff_ref = get_ref(f'staff/{staff_id}')
        if not staff_ref.get():
            raise HTTPException(status_code=404, detail=f"Staff member {staff_id} not found")
        schedule_ref = staff_ref.child('schedule')
        schedule_ref.child(date).set(shift)
        return {"message": "Schedule updated successfully"}
    except Exception as e:
        logger.error(f"Error updating staff schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/load")
async def get_staff_load():
    """Get current staff workload by department"""
    try:
        staff_ref = get_ref('staff')
        staff_data = staff_ref.get()
        
        if not staff_data:
            return {}
            
        # Calculate average workload by department
        department_loads = {}
        department_counts = {}
        
        for staff in staff_data.values():
            if 'currentStatus' in staff and 'personalInfo' in staff:
                dept = staff['personalInfo'].get('department')
                workload = staff['currentStatus'].get('workload', 0)
                
                if dept:
                    department_loads[dept] = department_loads.get(dept, 0) + workload
                    department_counts[dept] = department_counts.get(dept, 0) + 1
        
        # Calculate averages
        average_loads = {
            dept: round(total_load / department_counts[dept], 2)
            for dept, total_load in department_loads.items()
        }
        
        return average_loads
    except Exception as e:
        logger.error(f"Error calculating staff load: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{staff_id}/patients")
async def get_staff_patients(staff_id: str):
    """Get list of patients assigned to staff member"""
    try:
        staff_ref = get_ref(f'staff/{staff_id}')
        staff_data = staff_ref.get()
        
        if not staff_data:
            raise HTTPException(status_code=404, detail=f"Staff member {staff_id} not found")
            
        # Get current assignments
        current_date = datetime.now().strftime("%Y-%m-%d")
        schedule = staff_data.get('schedule', {}).get(current_date, {})
        patient_ids = schedule.get('patientAssignments', [])
        
        # Fetch patient details
        patients_ref = get_ref('patients')
        patients_data = {}
        
        for patient_id in patient_ids:
            patient_data = patients_ref.child(patient_id).get()
            if patient_data:
                patients_data[patient_id] = patient_data
                
        return patients_data
    except Exception as e:
        logger.error(f"Error fetching staff patients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{staff_id}/status")
async def update_staff_status(staff_id: str, status: dict):
    """Update staff member's current status (no validation)"""
    try:
        staff_ref = get_ref(f'staff/{staff_id}')
        if not staff_ref.get():
            raise HTTPException(status_code=404, detail=f"Staff member {staff_id} not found")
        status_ref = staff_ref.child('currentStatus')
        status_ref.set(status)
        return {"message": "Status updated successfully"}
    except Exception as e:
        logger.error(f"Error updating staff status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
