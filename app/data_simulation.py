import os
import json
import time
import random
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List
import threading
import logging
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db
from vitals_simulator import VitalsSimulator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_requested = True

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def format_datetime_for_firebase(dt):
    """Format datetime in a Firebase-safe format (no colons or special chars)"""
    return dt.strftime("%Y-%m-%d_%H-%M-%S")

class HospitalDataSimulator:
    def __init__(self):
        self.init_firebase()
        self.simulator = VitalsSimulator()
        
    def init_firebase(self):
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

    def get_existing_monitors(self) -> List[Dict]:
        """Get list of existing IoT monitors and their assigned patients"""
        try:
            iot_ref = db.reference('iotData')
            monitors_data = iot_ref.get()
            if not monitors_data:
                logger.error("No IoT monitors found in database")
                return []
            
            monitors = []
            for monitor_id, data in monitors_data.items():
                if 'deviceInfo' in data and 'vitals' in data:
                    monitors.append({
                        'id': monitor_id,
                        'roomId': data['deviceInfo'].get('roomId'),
                        'bedId': data['deviceInfo'].get('bedId'),
                        'patientId': next(iter(data['vitals'].values())).get('patientId') if data['vitals'] else None
                    })
            return monitors
        except Exception as e:
            logger.error(f"Error getting existing monitors: {str(e)}")
            return []

    def simulate_vitals_for_monitor(self, monitor: Dict):
        """Simulate and update vitals for a single monitor"""
        try:
            current_time = datetime.now()
            vitals = {
                'heartRate': 75 + random.randint(-5, 5),
                'oxygenLevel': 98 + random.uniform(-1, 1),
                'temperature': 37.0 + random.uniform(-0.3, 0.3),
                'bloodPressure': {
                    'systolic': 120 + random.randint(-10, 10),
                    'diastolic': 80 + random.randint(-5, 5)
                },
                'respiratoryRate': 16 + random.randint(-2, 2),
                'glucose': 100 + random.randint(-15, 15),
                'bedOccupancy': True,
                'patientId': monitor['patientId'],
                'deviceStatus': 'online',
                'batteryLevel': 85 + random.randint(0, 14),
                'signalStrength': 85 + random.randint(0, 14),
                'timestamp': format_datetime_for_firebase(current_time)
            }
            
            # Update vitals in Firebase using correct structure: vitals/{patient_id}/{timestamp}
            monitor_ref = db.reference(f'iotData/{monitor["id"]}/vitals/{monitor["patientId"]}')
            monitor_ref.child(format_datetime_for_firebase(current_time)).set(vitals)
            logger.info(f"Updated vitals for monitor {monitor['id']}")
            
        except Exception as e:
            logger.error(f"Error updating vitals for monitor {monitor['id']}: {str(e)}")

    def start_vitals_simulation(self):
        """Start simulating vitals for all monitors"""
        global shutdown_requested
        logger.info("Starting vitals simulation...")
        
        while not shutdown_requested:
            try:
                monitors = self.get_existing_monitors()
                if not monitors:
                    logger.warning("No monitors found to simulate vitals")
                    time.sleep(5)
                    continue
                
                for monitor in monitors:
                    if shutdown_requested:
                        break
                    if monitor['patientId']:  # Only simulate if monitor has assigned patient
                        self.simulate_vitals_for_monitor(monitor)
                
                # Sleep with periodic checks for shutdown
                for _ in range(5):  # Check every second for 5 seconds total
                    if shutdown_requested:
                        break
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in vitals simulation: {str(e)}")
                if not shutdown_requested:
                    time.sleep(5)
        
        logger.info("Vitals simulation stopped gracefully")

def main():
    """Main function to start the vitals simulation"""
    try:
        logger.info("Initializing Hospital Data Simulator...")
        simulator = HospitalDataSimulator()
        simulator.start_vitals_simulation()
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
    except Exception as e:
        logger.error(f"Error in simulation: {str(e)}")
    finally:
        logger.info("Simulation terminated")

if __name__ == "__main__":
    main() 