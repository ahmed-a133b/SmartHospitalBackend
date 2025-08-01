from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
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

@router.get("/stats")
async def get_staff_statistics():
    """Get comprehensive staff statistics for dashboard"""
    try:
        staff_ref = get_ref('staff')
        staff_data = staff_ref.get()
        
        if not staff_data:
            return {
                "total_staff": 0,
                "on_duty_count": 0,
                "by_role": {},
                "by_department": {},
                "average_workload": 0,
                "shift_distribution": {}
            }
        
        stats = {
            "total_staff": len(staff_data),
            "on_duty_count": 0,
            "by_role": {},
            "by_department": {},
            "average_workload": 0,
            "shift_distribution": {"day": 0, "night": 0, "on-call": 0}
        }
        
        total_workload = 0
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        for staff in staff_data.values():
            personal_info = staff.get('personalInfo', {})
            current_status = staff.get('currentStatus', {})
            schedule = staff.get('schedule', {})
            
            # Count by role
            role = personal_info.get('role', 'unknown')
            stats["by_role"][role] = stats["by_role"].get(role, 0) + 1
            
            # Count by department
            department = personal_info.get('department', 'unknown')
            stats["by_department"][department] = stats["by_department"].get(department, 0) + 1
            
            # On duty count
            if current_status.get('onDuty', False):
                stats["on_duty_count"] += 1
            
            # Workload calculation
            workload = current_status.get('workload', 0)
            total_workload += workload
            
            # Shift distribution for today
            today_schedule = schedule.get(current_date, {})
            shift_type = today_schedule.get('shiftType', '')
            if shift_type in stats["shift_distribution"]:
                stats["shift_distribution"][shift_type] += 1
        
        # Calculate average workload
        if stats["total_staff"] > 0:
            stats["average_workload"] = round(total_workload / stats["total_staff"], 2)
        
        return stats
    except Exception as e:
        logger.error(f"Error fetching staff statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/on-duty")
async def get_on_duty_staff():
    """Get all currently on-duty staff members"""
    try:
        staff_ref = get_ref('staff')
        staff_data = staff_ref.get()
        
        if not staff_data:
            return {}
        
        on_duty_staff = {}
        for staff_id, staff in staff_data.items():
            if staff.get('currentStatus', {}).get('onDuty', False):
                on_duty_staff[staff_id] = staff
        
        return on_duty_staff
    except Exception as e:
        logger.error(f"Error fetching on-duty staff: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-ward/{ward_id}")
async def get_staff_by_ward(ward_id: str):
    """Get all staff assigned to a specific ward"""
    try:
        staff_ref = get_ref('staff')
        staff_data = staff_ref.get()
        
        if not staff_data:
            return {}
        
        ward_staff = {}
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        for staff_id, staff in staff_data.items():
            schedule = staff.get('schedule', {})
            today_schedule = schedule.get(current_date, {})
            
            if today_schedule.get('ward') == ward_id:
                ward_staff[staff_id] = staff
        
        return ward_staff
    except Exception as e:
        logger.error(f"Error fetching ward staff: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{staff_id}/duty-status")
async def toggle_duty_status(staff_id: str, on_duty: bool):
    """Toggle staff member's duty status"""
    try:
        staff_ref = get_ref(f'staff/{staff_id}')
        staff_data = staff_ref.get()
        
        if not staff_data:
            raise HTTPException(status_code=404, detail=f"Staff member {staff_id} not found")
        
        # Update duty status with timestamp
        status_update = {
            'onDuty': on_duty,
            'lastUpdated': datetime.now().isoformat()
        }
        
        status_ref = staff_ref.child('currentStatus')
        status_ref.update(status_update)
        
        return {
            "message": f"Staff duty status updated to {'on duty' if on_duty else 'off duty'}",
            "staff_id": staff_id,
            "on_duty": on_duty
        }
    except Exception as e:
        logger.error(f"Error updating duty status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{staff_id}/workload-history")
async def get_staff_workload_history(
    staff_id: str,
    days: int = Query(7, description="Number of days to look back")
):
    """Get staff workload history for analytics"""
    try:
        staff_ref = get_ref(f'staff/{staff_id}')
        staff_data = staff_ref.get()
        
        if not staff_data:
            raise HTTPException(status_code=404, detail=f"Staff member {staff_id} not found")
        
        # For now, return current workload as historical data would require time-series storage
        # This is a placeholder that can be enhanced with actual historical data collection
        current_workload = staff_data.get('currentStatus', {}).get('workload', 0)
        
        history = []
        for i in range(days):
            date_offset = datetime.now().date() - timedelta(days=i)
            history.append({
                "date": date_offset.isoformat(),
                "workload": current_workload + (i * 2),  # Mock variation
                "hours_worked": 8 if current_workload > 0 else 0
            })
        
        return {
            "staff_id": staff_id,
            "history": history[::-1],  # Reverse to get chronological order
            "average_workload": sum(h["workload"] for h in history) / len(history)
        }
    except Exception as e:
        logger.error(f"Error fetching workload history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{staff_id}/schedule/bulk")
async def update_bulk_schedule(staff_id: str, schedule_data: dict):
    """Update multiple days of schedule at once"""
    try:
        staff_ref = get_ref(f'staff/{staff_id}')
        if not staff_ref.get():
            raise HTTPException(status_code=404, detail=f"Staff member {staff_id} not found")
        
        schedule_ref = staff_ref.child('schedule')
        
        # Update multiple dates
        for date_str, shift_data in schedule_data.items():
            schedule_ref.child(date_str).set(shift_data)
        
        return {
            "message": f"Bulk schedule updated for {len(schedule_data)} days",
            "staff_id": staff_id,
            "updated_dates": list(schedule_data.keys())
        }
    except Exception as e:
        logger.error(f"Error updating bulk schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/departments")
async def get_departments():
    """Get list of all departments with staff counts"""
    try:
        staff_ref = get_ref('staff')
        staff_data = staff_ref.get()
        
        if not staff_data:
            return {}
        
        departments = {}
        for staff in staff_data.values():
            dept = staff.get('personalInfo', {}).get('department')
            if dept:
                if dept not in departments:
                    departments[dept] = {
                        "name": dept,
                        "total_staff": 0,
                        "on_duty": 0,
                        "roles": {}
                    }
                
                departments[dept]["total_staff"] += 1
                
                if staff.get('currentStatus', {}).get('onDuty', False):
                    departments[dept]["on_duty"] += 1
                
                role = staff.get('personalInfo', {}).get('role', 'unknown')
                departments[dept]["roles"][role] = departments[dept]["roles"].get(role, 0) + 1
        
        return departments
    except Exception as e:
        logger.error(f"Error fetching departments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_staff(
    query: str = Query(..., description="Search query for staff name, role, or department"),
    limit: int = Query(20, description="Maximum number of results")
):
    """Search staff members by name, role, or department"""
    try:
        staff_ref = get_ref('staff')
        staff_data = staff_ref.get()
        
        if not staff_data:
            return {}
        
        query_lower = query.lower()
        matching_staff = {}
        count = 0
        
        for staff_id, staff in staff_data.items():
            if count >= limit:
                break
                
            personal_info = staff.get('personalInfo', {})
            name = personal_info.get('name', '').lower()
            role = personal_info.get('role', '').lower()
            department = personal_info.get('department', '').lower()
            specialization = personal_info.get('specialization', '').lower()
            
            if (query_lower in name or 
                query_lower in role or 
                query_lower in department or 
                query_lower in specialization):
                matching_staff[staff_id] = staff
                count += 1
        
        return matching_staff
    except Exception as e:
        logger.error(f"Error searching staff: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
