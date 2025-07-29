"""
Environmental Sensors Data Initialization Script

This script adds initial environmental sensor data to the Firebase database.
It creates environmental sensors for different rooms with realistic readings
including temperature, humidity, air quality, light level, noise level,
atmospheric pressure, and CO2 levels.
"""

import os
import sys
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the app directory to the Python path
app_dir = os.path.join(os.path.dirname(__file__), 'app')
sys.path.insert(0, app_dir)

try:
    from firebase_config import init_firebase, get_ref
except ImportError:
    print("❌ Error: Cannot import firebase_config. Make sure app/firebase_config.py exists.")
    sys.exit(1)

# Load environment variables
load_dotenv()

def format_datetime_for_firebase(dt):
    """Format datetime in a Firebase-safe format (no colons or special chars)"""
    return dt.strftime("%Y-%m-%d_%H-%M-%S")

def generate_environmental_reading(time_offset_minutes=0):
    """
    Generate realistic environmental readings using general room configuration
    
    Args:
        time_offset_minutes: Minutes to subtract from current time
    
    Returns:
        Dictionary containing environmental sensor readings
    """
    current_time = datetime.now() - timedelta(minutes=time_offset_minutes)
    
    # General room configuration for all sensors
    config = {
        "temperature": (20.0, 26.0),
        "humidity": (40, 60),
        "airQuality": (90, 98),
        "lightLevel": (75, 95),
        "noiseLevel": (30, 50),
        "pressure": (1011.0, 1016.0),
        "co2Level": (380, 500)
    }
    
    return {
        "temperature": round(random.uniform(*config["temperature"]), 1),
        "humidity": random.randint(*config["humidity"]),
        "airQuality": random.randint(*config["airQuality"]),
        "lightLevel": random.randint(*config["lightLevel"]),
        "noiseLevel": random.randint(*config["noiseLevel"]),
        "pressure": round(random.uniform(*config["pressure"]), 2),
        "co2Level": random.randint(*config["co2Level"]),
        "deviceStatus": "online",
        "batteryLevel": random.randint(75, 95),
        "signalStrength": random.randint(85, 98),
        "timestamp": format_datetime_for_firebase(current_time)
    }

def create_environmental_sensors():
    """Create environmental sensor data for different rooms"""
    current_time = datetime.now()
    
    environmental_sensors = {
        "env_sensor_1": {
            "vitals": {},
            "deviceInfo": {
                "type": "environmental_sensor",
                "manufacturer": "EnviroTech Solutions",
                "model": "ET-ENV-2024",
                "roomId": "room_1",
                "lastCalibrated": format_datetime_for_firebase(current_time - timedelta(days=15)),
                "calibrationDue": format_datetime_for_firebase(current_time + timedelta(days=75)),
                "maintenanceSchedule": format_datetime_for_firebase(current_time + timedelta(days=180)),
                "installationDate": format_datetime_for_firebase(current_time - timedelta(days=365))
            },
            "alerts": {}
        },
        "env_sensor_2": {
            "vitals": {},
            "deviceInfo": {
                "type": "environmental_sensor",
                "manufacturer": "EnviroTech Solutions",
                "model": "ET-ENV-2024",
                "roomId": "room_2",
                "lastCalibrated": format_datetime_for_firebase(current_time - timedelta(days=10)),
                "calibrationDue": format_datetime_for_firebase(current_time + timedelta(days=80)),
                "maintenanceSchedule": format_datetime_for_firebase(current_time + timedelta(days=175)),
                "installationDate": format_datetime_for_firebase(current_time - timedelta(days=300))
            },
            "alerts": {}
        },
        "env_sensor_3": {
            "vitals": {},
            "deviceInfo": {
                "type": "environmental_sensor",
                "manufacturer": "EnviroTech Solutions", 
                "model": "ET-ENV-2024",
                "roomId": "room_3",
                "lastCalibrated": format_datetime_for_firebase(current_time - timedelta(days=20)),
                "calibrationDue": format_datetime_for_firebase(current_time + timedelta(days=70)),
                "maintenanceSchedule": format_datetime_for_firebase(current_time + timedelta(days=170)),
                "installationDate": format_datetime_for_firebase(current_time - timedelta(days=400))
            },
            "alerts": {}
        },
        "env_sensor_4": {
            "vitals": {},
            "deviceInfo": {
                "type": "environmental_sensor",
                "manufacturer": "EnviroTech Solutions",
                "model": "ET-ENV-2024",
                "roomId": "room_4",
                "lastCalibrated": format_datetime_for_firebase(current_time - timedelta(days=5)),
                "calibrationDue": format_datetime_for_firebase(current_time + timedelta(days=85)),
                "maintenanceSchedule": format_datetime_for_firebase(current_time + timedelta(days=185)),
                "installationDate": format_datetime_for_firebase(current_time - timedelta(days=200))
            },
            "alerts": {}
        },
        "env_sensor_5": {
            "vitals": {},
            "deviceInfo": {
                "type": "environmental_sensor",
                "manufacturer": "AirQuality Pro",
                "model": "AQ-MONITOR-2024", 
                "roomId": "room_5",
                "lastCalibrated": format_datetime_for_firebase(current_time - timedelta(days=8)),
                "calibrationDue": format_datetime_for_firebase(current_time + timedelta(days=82)),
                "maintenanceSchedule": format_datetime_for_firebase(current_time + timedelta(days=178)),
                "installationDate": format_datetime_for_firebase(current_time - timedelta(days=250))
            },
            "alerts": {}
        }
    }
    
    # Room type mapping for realistic readings (now using general config for all)
    room_types = {
        "env_sensor_1": "general",      # Room 1
        "env_sensor_2": "general",      # Room 2
        "env_sensor_3": "general",      # Room 3
        "env_sensor_4": "general",      # Room 4
        "env_sensor_5": "general"       # Room 5
    }
    
    # Generate historical readings (last 24 hours)
    time_intervals = [0, 15, 30, 60, 120, 240, 480, 720, 1440]  # minutes ago
    
    for sensor_id, sensor_data in environmental_sensors.items():
        for time_offset in time_intervals:
            timestamp = format_datetime_for_firebase(current_time - timedelta(minutes=time_offset))
            reading = generate_environmental_reading(time_offset)
            sensor_data["vitals"][timestamp] = reading
    
    return environmental_sensors

def add_environmental_alerts():
    """Add some sample environmental alerts with timestamps"""
    current_time = datetime.now()
    
    alerts = {
        "env_sensor_2": {
            "alerts": {
                format_datetime_for_firebase(current_time - timedelta(minutes=45)): {
                    "type": "warning",
                    "message": "CO2 levels slightly elevated - 480 ppm",
                    "timestamp": format_datetime_for_firebase(current_time - timedelta(minutes=45)),
                    "resolved": True,
                    "resolvedBy": "staff_2",
                    "resolvedAt": format_datetime_for_firebase(current_time - timedelta(minutes=30)),
                    "category": "environmental"
                }
            }
        },
        "env_sensor_4": {
            "alerts": {
                format_datetime_for_firebase(current_time - timedelta(hours=2)): {
                    "type": "info",
                    "message": "Calibration due in 7 days",
                    "timestamp": format_datetime_for_firebase(current_time - timedelta(hours=2)),
                    "resolved": False,
                    "assignedTo": "staff_3",
                    "category": "maintenance"
                }
            }
        }
    }
    
    return alerts

def main():
    """Main function to initialize environmental sensors in the database"""
    try:
        print("🔧 Initializing Firebase connection...")
        init_firebase()
        print("✅ Firebase connected successfully!")
        
        print("\n🌱 Generating environmental sensor data...")
        env_sensors = create_environmental_sensors()
        
        print("📊 Generating environmental alerts...")
        alerts = add_environmental_alerts()
        
        # Merge alerts into sensor data
        for sensor_id, alert_data in alerts.items():
            if sensor_id in env_sensors:
                env_sensors[sensor_id]["alerts"] = alert_data["alerts"]
        
        print(f"\n📡 Adding {len(env_sensors)} environmental sensors to database...")
        
        # Add each sensor to the database
        iot_ref = get_ref('iotData')
        
        for sensor_id, sensor_data in env_sensors.items():
            print(f"  📍 Adding {sensor_id} ({sensor_data['deviceInfo']['roomId']})...")
            sensor_ref = iot_ref.child(sensor_id)
            sensor_ref.set(sensor_data)
            
        print("\n✅ Environmental sensors added successfully!")
        print("\n📈 Summary:")
        print(f"  • {len(env_sensors)} environmental sensors")
        print(f"  • {sum(len(s['vitals']) for s in env_sensors.values())} total readings")
        print(f"  • {sum(len(s.get('alerts', {})) for s in env_sensors.values())} alerts")
        
        print("\n🏥 Sensor locations:")
        for sensor_id, sensor_data in env_sensors.items():
            room_id = sensor_data['deviceInfo']['roomId']
            print(f"  • {sensor_id}: {room_id}")
            
        print("\n🌟 Environmental monitoring system is now active!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
