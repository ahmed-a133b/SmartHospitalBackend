from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.firebase_config import get_ref
import uuid
from datetime import datetime

router = APIRouter(prefix="/rooms", tags=["rooms"])

class RoomData(BaseModel):
    roomId: str
    roomType: str  # 'ICU', 'ER', 'surgery', 'isolation', 'general'
    floor: int
    capacity: int
    assignedPatient: Optional[str] = None
    assignedDevices: List[str] = []
    status: str  # 'available', 'occupied', 'maintenance', 'reserved'
    description: Optional[str] = None

@router.get("/")
async def get_all_rooms():
    """Get all rooms"""
    try:
        ref = get_ref("rooms")
        rooms = ref.get() or {}
        return rooms
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch rooms: {str(e)}")

@router.get("/{room_id}")
async def get_room(room_id: str):
    """Get a specific room by ID"""
    try:
        ref = get_ref(f"rooms/{room_id}")
        room = ref.get()
        
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
            
        return room
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch room: {str(e)}")
@router.get("/{room_id}/devices")
async def get_room_devices(room_id: str):
    """Get all IoT devices assigned to a specific room"""
    try:
        # Check if room exists
        room_ref = get_ref(f"rooms/{room_id}")
        room_data = room_ref.get()
        if not room_data:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Get all IoT devices
        iot_ref = get_ref("iotData")
        all_devices = iot_ref.get() or {}
        
        # Filter devices assigned to this room
        room_devices = {}
        for device_id, device_data in all_devices.items():
            device_info = device_data.get('deviceInfo', {})
            device_room_id = device_info.get('roomId')
            
            if device_room_id == room_id:
                room_devices[device_id] = device_data
        
        return {
            "roomId": room_id,
            "deviceCount": len(room_devices),
            "devices": room_devices
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch room devices: {str(e)}")

@router.post("/")
async def create_room(room_data: RoomData):
    """Create a new room"""
    try:
        # Check if room already exists
        existing_room_ref = get_ref(f"rooms/{room_data.roomId}")
        existing_room = existing_room_ref.get()
        if existing_room:
            raise HTTPException(status_code=400, detail="Room already exists")
        
        # Prepare room data
        room_dict = room_data.dict()
        room_dict['createdAt'] = datetime.now().isoformat()
        room_dict['updatedAt'] = datetime.now().isoformat()
        
        # Create room document
        room_ref = get_ref(f"rooms/{room_data.roomId}")
        room_ref.set(room_dict)
        
        # Update patient assignment if provided
        if room_data.assignedPatient:
            await assign_patient_to_room(room_data.roomId, room_data.assignedPatient)
        
        # Update device assignments if provided
        for device_id in room_data.assignedDevices:
            await assign_device_to_room(room_data.roomId, device_id)
        
        return {"message": "Room created successfully", "roomId": room_data.roomId}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create room: {str(e)}")

@router.put("/{room_id}")
async def update_room(room_id: str, room_data: RoomData):
    """Update an existing room"""
    try:
        # Check if room exists
        room_ref = get_ref(f"rooms/{room_id}")
        current_data = room_ref.get()
        if not current_data:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Prepare updated data
        room_dict = room_data.dict()
        room_dict['updatedAt'] = datetime.now().isoformat()
        room_dict['createdAt'] = current_data.get('createdAt', datetime.now().isoformat())
        
        # Update room document
        room_ref.set(room_dict)
        
        # Handle patient assignment changes
        current_patient = current_data.get('assignedPatient')
        new_patient = room_data.assignedPatient
        
        if current_patient != new_patient:
            # Remove old patient assignment
            if current_patient:
                await unassign_patient_from_room(current_patient)
            
            # Add new patient assignment
            if new_patient:
                await assign_patient_to_room(room_id, new_patient)
        
        # Handle device assignment changes
        current_devices = set(current_data.get('assignedDevices', []))
        new_devices = set(room_data.assignedDevices)
        
        # Remove devices that are no longer assigned
        for device_id in current_devices - new_devices:
            await unassign_device_from_room(device_id)
        
        # Add new device assignments
        for device_id in new_devices - current_devices:
            await assign_device_to_room(room_id, device_id)
        
        return {"message": "Room updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update room: {str(e)}")
        
        # Handle patient assignment changes
        current_patient = current_data.get('assignedPatient')
        new_patient = room_data.assignedPatient
        
        if current_patient != new_patient:
            # Remove old patient assignment
            if current_patient:
                await unassign_patient_from_room(current_patient)
            
            # Add new patient assignment
            if new_patient:
                await assign_patient_to_room(room_id, new_patient)
        
        # Handle device assignment changes
        current_devices = set(current_data.get('assignedDevices', []))
        new_devices = set(room_data.assignedDevices)
        
        # Remove devices that are no longer assigned
        for device_id in current_devices - new_devices:
            await unassign_device_from_room(device_id)
        
        # Add new device assignments
        for device_id in new_devices - current_devices:
            await assign_device_to_room(room_id, device_id)
        
        return {"message": "Room updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update room: {str(e)}")

@router.delete("/{room_id}")
async def delete_room(room_id: str):
    """Delete a room"""
    try:
        # Check if room exists
        room_ref = get_ref(f"rooms/{room_id}")
        room_data = room_ref.get()
        if not room_data:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Unassign patient if assigned
        if room_data.get('assignedPatient'):
            await unassign_patient_from_room(room_data['assignedPatient'])
        
        # Unassign all devices
        for device_id in room_data.get('assignedDevices', []):
            await unassign_device_from_room(device_id)
        
        # Delete room
        room_ref.delete()
        
        return {"message": "Room deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete room: {str(e)}")

@router.post("/{room_id}/assign-patient/{patient_id}")
async def assign_patient_to_room_endpoint(room_id: str, patient_id: str):
    """Assign a patient to a room"""
    try:
        await assign_patient_to_room(room_id, patient_id)
        return {"message": "Patient assigned to room successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign patient: {str(e)}")

@router.post("/{room_id}/assign-device/{device_id}")
async def assign_device_to_room_endpoint(room_id: str, device_id: str):
    """Assign a device to a room"""
    try:
        await assign_device_to_room(room_id, device_id)
        return {"message": "Device assigned to room successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign device: {str(e)}")

@router.delete("/{room_id}/unassign-patient/{patient_id}")
async def unassign_patient_from_room_endpoint(patient_id: str):
    """Unassign a patient from a room"""
    try:
        await unassign_patient_from_room(patient_id)
        return {"message": "Patient unassigned from room successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unassign patient: {str(e)}")

@router.delete("/{room_id}/unassign-device/{device_id}")
async def unassign_device_from_room_endpoint(device_id: str):
    """Unassign a device from a room"""
    try:
        await unassign_device_from_room(device_id)
        return {"message": "Device unassigned from room successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unassign device: {str(e)}")

# Helper functions
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
        raise HTTPException(status_code=500, detail=f"Error finding available bed: {str(e)}")

async def assign_patient_to_room(room_id: str, patient_id: str):
    """Helper function to assign patient to room and find an available bed"""
    # Check if patient exists
    patient_ref = get_ref(f"patients/{patient_id}")
    patient_data = patient_ref.get()
    
    if not patient_data:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Find an available bed in the room
    available_bed_id = await find_available_bed_in_room(room_id)
    
    if not available_bed_id:
        raise HTTPException(status_code=400, detail=f"No available beds in room {room_id}")
    
    # Assign patient to the bed
    bed_ref = get_ref(f"beds/{available_bed_id}")
    bed_data = bed_ref.get()
    
    if not bed_data:
        raise HTTPException(status_code=404, detail=f"Bed {available_bed_id} not found")
    
    # Update bed status
    bed_data['patientId'] = patient_id
    bed_data['status'] = 'occupied'
    bed_ref.set(bed_data)
    
    # Update patient's bed and room assignment
    patient_data['personalInfo']['bedId'] = available_bed_id
    patient_data['personalInfo']['roomId'] = room_id
    patient_ref.set(patient_data)
    
    # Update room's patient assignment
    room_ref = get_ref(f"rooms/{room_id}")
    room_ref.update({'assignedPatient': patient_id, 'status': 'occupied'})

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
            assigned_patient = None
            
            # If room is occupied, find the assigned patient (for backward compatibility)
            if occupied_beds:
                assigned_patient = occupied_beds[0].get('patientId')
            
            room_ref.update({
                'status': new_status,
                'assignedPatient': assigned_patient
            })
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating room status: {str(e)}")

async def unassign_patient_from_room(patient_id: str):
    """Helper function to unassign patient from room and discharge from bed"""
    # Get current patient data
    patient_ref = get_ref(f"patients/{patient_id}")
    patient_data = patient_ref.get()
    
    if patient_data:
        old_room_id = patient_data.get('personalInfo', {}).get('roomId')
        old_bed_id = patient_data.get('personalInfo', {}).get('bedId')
        
        # Discharge from bed if assigned
        if old_bed_id:
            bed_ref = get_ref(f"beds/{old_bed_id}")
            bed_data = bed_ref.get()
            
            if bed_data:
                # Update bed status
                bed_data['patientId'] = None
                bed_data['status'] = 'available'
                bed_ref.set(bed_data)
        
        # Remove room and bed assignment from patient
        patient_data['personalInfo']['roomId'] = None
        patient_data['personalInfo']['bedId'] = None
        patient_ref.set(patient_data)
        
        # Update room status based on remaining bed occupancy
        if old_room_id:
            await update_room_status_based_on_beds(old_room_id)

async def assign_device_to_room(room_id: str, device_id: str):
    """Helper function to assign device to room"""
    # Update device's room assignment
    device_ref = get_ref(f"iotData/{device_id}")
    device_data = device_ref.get()
    
    if not device_data:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device_data['deviceInfo']['roomId'] = room_id
    device_ref.set(device_data)

async def unassign_device_from_room(device_id: str):
    """Helper function to unassign device from room"""
    # Remove room assignment from device
    device_ref = get_ref(f"iotData/{device_id}")
    device_data = device_ref.get()
    
    if device_data:
        device_data['deviceInfo']['roomId'] = None
        device_ref.set(device_data)

@router.get("/{room_id}/devices")
async def get_room_devices(room_id: str):
    """Get all IoT devices assigned to a specific room"""
    try:
        # Check if room exists
        room_ref = get_ref(f"rooms/{room_id}")
        room_data = room_ref.get()
        if not room_data:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Get all IoT devices
        iot_ref = get_ref("iotData")
        all_devices = iot_ref.get() or {}
        
        # Filter devices assigned to this room
        room_devices = {}
        for device_id, device_data in all_devices.items():
            device_info = device_data.get('deviceInfo', {})
            device_room_id = device_info.get('roomId')
            
            if device_room_id == room_id:
                room_devices[device_id] = device_data
        
        return {
            "roomId": room_id,
            "deviceCount": len(room_devices),
            "devices": room_devices
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch room devices: {str(e)}")

@router.get("/stats/occupancy")
async def get_room_occupancy_stats():
    """Get room occupancy statistics"""
    try:
        rooms_ref = get_ref("rooms")
        rooms = rooms_ref.get() or {}
        
        stats = {
            'total': 0,
            'occupied': 0,
            'available': 0,
            'maintenance': 0,
            'reserved': 0
        }
        
        for room_id, room_data in rooms.items():
            stats['total'] += 1
            status = room_data.get('status', 'available')
            if status in stats:
                stats[status] += 1
        
        stats['occupancy_rate'] = (stats['occupied'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get occupancy stats: {str(e)}")
