#!/usr/bin/env python3
"""
Initialize IoT devices with proper structure for testing
"""
import os
import json
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv

def init_firebase():
    """Initialize Firebase connection"""
    load_dotenv()
    json_str = os.getenv("FIREBASE_KEY_JSON")
    db_url = os.getenv("FIREBASE_DATABASE_URL")

    if not json_str or not db_url:
        raise ValueError("Missing FIREBASE_KEY_JSON or FIREBASE_DATABASE_URL")

    try:
        json_data = json.loads(json_str)  
        cred = credentials.Certificate(json_data)
        if not firebase_admin._apps:  # Only initialize if not already initialized
            firebase_admin.initialize_app(cred, {
                'databaseURL': db_url
            })
    except json.JSONDecodeError as e:
        raise ValueError("Invalid FIREBASE_KEY_JSON") from e

def create_sample_iot_devices():
    """Create sample IoT devices with proper structure"""
    
    devices = {
        "monitor_1": {
            "deviceInfo": {
                "type": "vitals_monitor",
                "manufacturer": "MedTech",
                "model": "VM-2000",
                "roomId": "101",
                "bedId": "A",
                "lastCalibrated": "2025-01-01T00:00:00Z",
                "calibrationDue": "2025-07-01T00:00:00Z",
                "maintenanceSchedule": "2025-12-01T00:00:00Z"
            },
            "vitals": {},
            "alerts": {}
        },
        "monitor_2": {
            "deviceInfo": {
                "type": "vitals_monitor",
                "manufacturer": "HealthCorp",
                "model": "HC-150",
                "roomId": "102",
                "bedId": "B",
                "lastCalibrated": "2025-01-01T00:00:00Z",
                "calibrationDue": "2025-07-01T00:00:00Z",
                "maintenanceSchedule": "2025-12-01T00:00:00Z"
            },
            "vitals": {},
            "alerts": {}
        },
        "monitor_3": {
            "deviceInfo": {
                "type": "bed_sensor",
                "manufacturer": "SmartBed",
                "model": "SB-300",
                "roomId": "103",
                "bedId": "A",
                "lastCalibrated": "2025-01-01T00:00:00Z",
                "calibrationDue": "2025-07-01T00:00:00Z",
                "maintenanceSchedule": "2025-12-01T00:00:00Z"
            },
            "vitals": {},
            "alerts": {}
        }
    }
    
    # Add some sample vitals and alerts
    current_time = datetime.now()
    timestamp = current_time.isoformat().replace(':', '-').replace('.', '-')
    
    # Add sample vitals for monitor_1
    devices["monitor_1"]["vitals"][timestamp] = {
        "heartRate": 75,
        "oxygenLevel": 98.5,
        "temperature": 36.8,
        "bloodPressure": {
            "systolic": 120,
            "diastolic": 80
        },
        "respiratoryRate": 16,
        "glucose": 95,
        "bedOccupancy": True,
        "patientId": "patient_001",
        "deviceStatus": "online",
        "batteryLevel": 85,
        "signalStrength": 90,
        "timestamp": current_time.isoformat()
    }
    
    # Add sample alert for monitor_2
    alert_time = (current_time - timedelta(minutes=30)).isoformat().replace(':', '-').replace('.', '-')
    devices["monitor_2"]["alerts"][alert_time] = {
        "type": "warning",
        "message": "Heart rate elevated - 105 bpm",
        "timestamp": (current_time - timedelta(minutes=30)).isoformat(),
        "resolved": False,
        "resolvedBy": None,
        "resolvedAt": None,
        "assignedTo": None
    }
    
    # Add resolved alert for monitor_1
    resolved_alert_time = (current_time - timedelta(hours=2)).isoformat().replace(':', '-').replace('.', '-')
    devices["monitor_1"]["alerts"][resolved_alert_time] = {
        "type": "critical",
        "message": "Oxygen level low - 88%",
        "timestamp": (current_time - timedelta(hours=2)).isoformat(),
        "resolved": True,
        "resolvedBy": "Dr. Smith",
        "resolvedAt": (current_time - timedelta(hours=1, minutes=30)).isoformat(),
        "assignedTo": "nurse_jane"
    }
    
    return devices

def main():
    """Initialize Firebase and create sample data"""
    try:
        init_firebase()
        print("✓ Firebase initialized")
        
        # Create sample devices
        devices = create_sample_iot_devices()
        
        # Save to Firebase
        iot_ref = db.reference('iotData')
        for device_id, device_data in devices.items():
            iot_ref.child(device_id).set(device_data)
            print(f"✓ Created device: {device_id}")
        
        print(f"\n✓ Successfully initialized {len(devices)} IoT devices")
        print("✓ Sample vitals and alerts added")
        
        # Display summary
        print("\nDevice Summary:")
        for device_id, device_data in devices.items():
            device_info = device_data['deviceInfo']
            vitals_count = len(device_data['vitals'])
            alerts_count = len(device_data['alerts'])
            print(f"  {device_id}: {device_info['type']} in Room {device_info['roomId']} - {vitals_count} vitals, {alerts_count} alerts")
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    main()
