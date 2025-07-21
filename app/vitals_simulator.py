import time
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
import logging
import re
from firebase_admin import db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VitalsSimulator:
    def __init__(self):
        self.running = False
        self.simulation_threads = []
        self.monitors = {}  # Will store monitor-patient mappings
        self.patients = {}  # Will store patient data
        self.patient_vitals_cache = {}  # Cache for current vital values
        
    def fetch_monitor_data(self) -> bool:
        """Fetch monitor data and their assigned patients from Firebase"""
        try:
            iot_ref = db.reference('iotData')
            monitors_data = iot_ref.get()
            
            if monitors_data:
                logger.info(f"Successfully fetched {len(monitors_data)} monitors from database")
                
                # Store monitor-patient mappings and fetch patient data
                for monitor_id, monitor_data in monitors_data.items():
                    # Get the latest vitals entry if it exists
                    vitals = monitor_data.get('vitals', {})
                    latest_vitals = None
                    if vitals:
                        # Get the latest timestamp's data
                        latest_timestamp = max(vitals.keys())
                        latest_vitals = vitals[latest_timestamp]
                    
                    # Get patient ID from latest vitals or device info
                    patient_id = None
                    if latest_vitals and 'patientId' in latest_vitals:
                        patient_id = latest_vitals['patientId']
                    
                    if patient_id:
                        self.monitors[monitor_id] = {
                            'patientId': patient_id,
                            'deviceInfo': monitor_data.get('deviceInfo', {}),
                            'lastVitals': latest_vitals
                        }
                        
                        # Fetch patient data if we haven't already
                        if patient_id not in self.patients:
                            patient_ref = db.reference(f'patients/{patient_id}')
                            patient_data = patient_ref.get()
                            if patient_data:
                                self.patients[patient_id] = self.convert_db_patient_to_simulation_format(patient_data)
                                # Initialize vitals cache from last reading if available
                                if latest_vitals:
                                    self.patient_vitals_cache[patient_id] = self.convert_vitals_to_cache_format(latest_vitals)
                                else:
                                    self.patient_vitals_cache[patient_id] = self.get_initial_vitals_for_patient(patient_data)
                
                return bool(self.monitors)
            else:
                logger.error("No monitors found in database")
                return False
                
        except Exception as e:
            logger.error(f"Error fetching monitor data: {str(e)}")
            return False
    
    def convert_db_patient_to_simulation_format(self, patient_data: Dict) -> Dict:
        """Convert database patient format to simulation format"""
        personal_info = patient_data.get('personalInfo', {})
        medical_history = patient_data.get('medicalHistory', {})
        current_status = patient_data.get('currentStatus', {})
        
        # Extract conditions and medications
        conditions = medical_history.get('conditions', [])
        medications = [med.get('name', '') for med in medical_history.get('medications', [])]
        
        # Determine patient state from current status
        status = current_status.get('status', 'stable').lower()
        state_mapping = {
            'stable': 'stable',
            'critical': 'critical',
            'improving': 'recovering',
            'deteriorating': 'deteriorating'
        }
        state = state_mapping.get(status, 'stable')
        
        # Get baseline vitals based on age and conditions
        age = personal_info.get('age', 50)
        baseline_vitals = self.get_baseline_vitals_for_patient(age, conditions)
        
        return {
            'name': personal_info.get('name', 'Unknown Patient'),
            'age': age,
            'conditions': conditions,
            'state': state,
            'medications': medications,
            'lastMedication': self.get_last_medication_time(medical_history.get('medications', [])),
            'baseline': baseline_vitals,
            'trends': self.initialize_trends_for_patient(state, conditions)
        }
    
    def convert_vitals_to_cache_format(self, vitals: Dict) -> Dict:
        """Convert vitals data from Firebase format to cache format"""
        return {
            'heartRate': vitals['heartRate'],
            'oxygenLevel': vitals['oxygenLevel'],
            'temperature': vitals['temperature'],
            'systolicBP': vitals['bloodPressure']['systolic'],
            'diastolicBP': vitals['bloodPressure']['diastolic'],
            'respiratoryRate': vitals['respiratoryRate'],
            'glucose': vitals['glucose']
        }
    
    def get_baseline_vitals_for_patient(self, age: int, conditions: List[str]) -> Dict:
        """Generate baseline vitals based on age and conditions"""
        # Age-based baseline adjustments
        if age < 18:
            base_hr = 90
            base_bp_sys = 105
            base_bp_dia = 65
        elif age < 65:
            base_hr = 70
            base_bp_sys = 120
            base_bp_dia = 80
        else:
            base_hr = 75
            base_bp_sys = 130
            base_bp_dia = 85
        
        baseline = {
            'heartRate': base_hr,
            'oxygenLevel': 98,
            'temperature': 37.0,
            'systolicBP': base_bp_sys,
            'diastolicBP': base_bp_dia,
            'respiratoryRate': 16,
            'glucose': 100
        }
        
        # Condition-based adjustments
        if 'hypertension' in conditions:
            baseline['systolicBP'] += 15
            baseline['diastolicBP'] += 10
        if 'diabetes' in conditions:
            baseline['glucose'] += 30
        if 'copd' in conditions:
            baseline['oxygenLevel'] -= 6
            baseline['respiratoryRate'] += 6
        if 'asthma' in conditions:
            baseline['oxygenLevel'] -= 2
            baseline['respiratoryRate'] += 2
        if 'cardiac_arrhythmia' in conditions:
            baseline['heartRate'] += 15
        
        return baseline
    
    def get_initial_vitals_for_patient(self, patient_data: Dict) -> Dict:
        """Get initial vitals values for a patient"""
        # Start with baseline values
        baseline = self.get_baseline_vitals_for_patient(
            patient_data.get('personalInfo', {}).get('age', 50),
            patient_data.get('medicalHistory', {}).get('conditions', [])
        )
        
        # Add some initial variation
        return {
            'heartRate': baseline['heartRate'] + random.randint(-5, 5),
            'oxygenLevel': baseline['oxygenLevel'] + random.uniform(-1, 1),
            'temperature': baseline['temperature'] + random.uniform(-0.3, 0.3),
            'systolicBP': baseline['systolicBP'] + random.randint(-10, 10),
            'diastolicBP': baseline['diastolicBP'] + random.randint(-5, 5),
            'respiratoryRate': baseline['respiratoryRate'] + random.randint(-2, 2),
            'glucose': baseline['glucose'] + random.randint(-15, 15)
        }
    
    def get_last_medication_time(self, medications: List[Dict]) -> datetime:
        """Get the last medication time from patient data"""
        if not medications:
            return datetime.now() - timedelta(hours=6)
        
        # Find the most recent medication
        latest_time = datetime.now() - timedelta(hours=6)
        for med in medications:
            if 'startDate' in med:
                try:
                    med_time = datetime.fromisoformat(med['startDate'].replace('Z', '+00:00'))
                    if med_time > latest_time:
                        latest_time = med_time
                except:
                    pass
        
        return latest_time
    
    def initialize_trends_for_patient(self, state: str, conditions: List[str]) -> Dict:
        """Initialize trends based on patient state and conditions"""
        trends = {
            'heartRate': {'direction': 0, 'magnitude': 2, 'duration': 0},
            'oxygenLevel': {'direction': 0, 'magnitude': 1, 'duration': 0},
            'temperature': {'direction': 0, 'magnitude': 0.2, 'duration': 0},
            'systolicBP': {'direction': 0, 'magnitude': 5, 'duration': 0},
            'diastolicBP': {'direction': 0, 'magnitude': 3, 'duration': 0},
            'respiratoryRate': {'direction': 0, 'magnitude': 1, 'duration': 0},
            'glucose': {'direction': 0, 'magnitude': 10, 'duration': 0}
        }
        
        # State-based trend initialization
        if state == 'critical':
            trends['heartRate']['direction'] = 1
            trends['heartRate']['duration'] = 10
            trends['oxygenLevel']['direction'] = -1
            trends['oxygenLevel']['duration'] = 8
            trends['respiratoryRate']['direction'] = 1
            trends['respiratoryRate']['duration'] = 12
        elif state == 'recovering':
            trends['oxygenLevel']['direction'] = 1
            trends['oxygenLevel']['duration'] = 5
            trends['respiratoryRate']['direction'] = -1
            trends['respiratoryRate']['duration'] = 3
        elif state == 'deteriorating':
            trends['temperature']['direction'] = 1
            trends['temperature']['duration'] = 8
            trends['heartRate']['direction'] = 1
            trends['heartRate']['duration'] = 6
        
        return trends

    def get_circadian_modifier(self, hour: int, vital_type: str) -> float:
        """Apply circadian rhythm effects to vitals"""
        patterns = {
            'heartRate': {'amplitude': 8, 'phase': 14, 'baseline': 1.0},
            'temperature': {'amplitude': 0.4, 'phase': 18, 'baseline': 1.0},
            'bloodPressure': {'amplitude': 12, 'phase': 10, 'baseline': 1.0}
        }
        
        pattern = patterns.get(vital_type)
        if not pattern:
            return 1.0
        
        radians = ((hour - pattern['phase']) * math.pi) / 12
        return pattern['baseline'] + (pattern['amplitude'] * math.cos(radians)) / 100

    def apply_condition_modifiers(self, value: float, vital_type: str, conditions: List[str]) -> float:
        """Apply medical condition effects to vitals"""
        modifiers = {
            'hypertension': {
                'systolicBP': 1.15,
                'diastolicBP': 1.12
            },
            'diabetes': {
                'glucose': 1.4,
                'temperature': 1.02
            },
            'copd': {
                'oxygenLevel': 0.95,
                'respiratoryRate': 1.25
            },
            'cardiac_arrhythmia': {
                'heartRate': 1.0
            },
            'asthma': {
                'oxygenLevel': 0.98,
                'respiratoryRate': 1.15
            }
        }
        
        modified = value
        for condition in conditions:
            if condition in modifiers and vital_type in modifiers[condition]:
                modified *= modifiers[condition][vital_type]
        
        return modified

    def generate_trend(self, current_value: float, baseline: float, trend: Dict, state: str) -> float:
        """Generate trending values based on patient state"""
        state_modifiers = {
            'stable': {'volatility': 0.02, 'trendStrength': 0.1},
            'recovering': {'volatility': 0.05, 'trendStrength': 0.3},
            'critical': {'volatility': 0.1, 'trendStrength': 0.5},
            'deteriorating': {'volatility': 0.08, 'trendStrength': 0.4}
        }
        
        modifier = state_modifiers.get(state, state_modifiers['stable'])
        
        # Apply existing trend
        new_value = current_value
        if trend['duration'] > 0:
            trend_effect = trend['direction'] * trend['magnitude'] * modifier['trendStrength']
            new_value += trend_effect
            trend['duration'] -= 1
        
        # Add noise
        noise = (random.random() - 0.5) * 2 * modifier['volatility'] * baseline
        new_value += noise
        
        # Gradually return to baseline
        return_force = (baseline - new_value) * 0.05
        new_value += return_force
        
        return new_value

    def correlate_vitals(self, vitals: Dict, patient: Dict) -> Dict:
        """Apply physiological correlations between vitals"""
        # Temperature affects heart rate
        temp_deviation = vitals['temperature'] - 37.0
        vitals['heartRate'] += temp_deviation * 8
        
        # Oxygen level affects heart rate (compensatory)
        if vitals['oxygenLevel'] < 95:
            compensation = (95 - vitals['oxygenLevel']) * 2
            vitals['heartRate'] += compensation
        
        # Heart rate affects blood pressure
        hr_deviation = (vitals['heartRate'] - patient['baseline']['heartRate']) / patient['baseline']['heartRate']
        vitals['systolicBP'] += hr_deviation * 20
        vitals['diastolicBP'] += hr_deviation * 10
        
        # Add arrhythmia irregularity
        if 'cardiac_arrhythmia' in patient['conditions']:
            if random.random() < 0.3:  # 30% chance of irregular beat
                vitals['heartRate'] += (random.random() - 0.5) * 40
        
        return vitals

    def check_medication_effects(self, vitals: Dict, patient: Dict) -> Dict:
        """Apply medication effects to vitals"""
        now = datetime.now()
        time_since_last_med = (now - patient['lastMedication']).total_seconds() / 60  # minutes
        
        effects = {
            'lisinopril': {
                'duration': 480,  # 8 hours
                'systolicBP': 0.9,
                'diastolicBP': 0.85
            },
            'metformin': {
                'duration': 360,  # 6 hours
                'glucose': 0.8
            },
            'albuterol': {
                'duration': 240,  # 4 hours
                'oxygenLevel': 1.03,
                'heartRate': 1.1
            },
            'digoxin': {
                'duration': 1440,  # 24 hours
                'heartRate': 0.9
            }
        }
        
        for med in patient['medications']:
            effect = effects.get(med)
            if effect and time_since_last_med < effect['duration']:
                # Apply medication effect
                strength = max(0.3, 1 - (time_since_last_med / effect['duration']))
                
                for vital, adjustment in effect.items():
                    if vital != 'duration' and vital in vitals:
                        adjustment_value = (adjustment - 1) * strength + 1
                        vitals[vital] *= adjustment_value
        
        return vitals

    def generate_emergency_scenario(self) -> Optional[str]:
        """Generate random emergency scenarios"""
        if random.random() < 0.001:  # 0.1% chance
            scenarios = ['cardiac_event', 'respiratory_distress', 'sepsis']
            return random.choice(scenarios)
        return None

    def apply_emergency_scenario(self, vitals: Dict, scenario: str, patient: Dict) -> Dict:
        """Apply emergency scenario effects"""
        emergency_effects = {
            'cardiac_event': {
                'heartRate': 0.3,
                'oxygenLevel': 0.85,
                'systolicBP': 0.6
            },
            'respiratory_distress': {
                'oxygenLevel': 0.82,
                'respiratoryRate': 2.0,
                'heartRate': 1.4
            },
            'sepsis': {
                'temperature': 1.08,
                'heartRate': 1.6,
                'systolicBP': 0.7
            }
        }
        
        effects = emergency_effects.get(scenario)
        if effects:
            for vital, multiplier in effects.items():
                if vital in vitals:
                    vitals[vital] *= multiplier
            
            patient['state'] = 'critical'
            logger.warning(f"EMERGENCY: {scenario} detected for {patient['name']}")
        
        return vitals

    def sanitize_timestamp(self, timestamp: str) -> str:
        """Convert ISO timestamp to a Firebase-safe string"""
        # Replace colons, periods, and other invalid characters
        sanitized = re.sub(r'[.:]', '-', timestamp)
        # Remove any other invalid characters for Firebase paths
        sanitized = re.sub(r'[#\$\[\]]', '', sanitized)
        return sanitized
    
    def generate_patient_vitals(self, patient_id: str) -> Optional[Dict]:
        """Generate realistic vitals for a patient"""
        patient = self.patients.get(patient_id)
        if not patient:
            return None
        
        now = datetime.now()
        hour = now.hour
        
        # Get current vitals from cache or initialize
        if patient_id not in self.patient_vitals_cache:
            self.patient_vitals_cache[patient_id] = dict(patient['baseline'])
        
        current_vitals = self.patient_vitals_cache[patient_id]
        
        # Generate new vitals based on current state
        vitals = dict(current_vitals)
        
        # Apply circadian rhythms
        vitals['heartRate'] *= self.get_circadian_modifier(hour, 'heartRate')
        vitals['temperature'] *= self.get_circadian_modifier(hour, 'temperature')
        vitals['systolicBP'] *= self.get_circadian_modifier(hour, 'bloodPressure')
        vitals['diastolicBP'] *= self.get_circadian_modifier(hour, 'bloodPressure')
        
        # Apply condition modifiers
        for vital in vitals:
            vitals[vital] = self.apply_condition_modifiers(vitals[vital], vital, patient['conditions'])
        
        # Apply trends
        for vital in vitals:
            if vital in patient['trends']:
                vitals[vital] = self.generate_trend(vitals[vital], patient['baseline'][vital], patient['trends'][vital], patient['state'])
        
        # Apply medication effects
        vitals = self.check_medication_effects(vitals, patient)
        
        # Apply physiological correlations
        vitals = self.correlate_vitals(vitals, patient)
        
        # Check for emergency scenarios
        emergency = self.generate_emergency_scenario()
        if emergency:
            vitals = self.apply_emergency_scenario(vitals, emergency, patient)
        
        # Apply realistic bounds
        vitals['heartRate'] = max(30, min(200, vitals['heartRate']))
        vitals['oxygenLevel'] = max(70, min(100, vitals['oxygenLevel']))
        vitals['temperature'] = max(32, min(42, vitals['temperature']))
        vitals['systolicBP'] = max(60, min(250, vitals['systolicBP']))
        vitals['diastolicBP'] = max(40, min(150, vitals['diastolicBP']))
        vitals['respiratoryRate'] = max(8, min(50, vitals['respiratoryRate']))
        vitals['glucose'] = max(40, min(600, vitals['glucose']))
        
        # Update cache
        self.patient_vitals_cache[patient_id] = vitals
        
        return {
            'heartRate': round(vitals['heartRate']),
            'oxygenLevel': round(vitals['oxygenLevel'] * 10) / 10,
            'temperature': round(vitals['temperature'] * 10) / 10,
            'bloodPressure': {
                'systolic': round(vitals['systolicBP']),
                'diastolic': round(vitals['diastolicBP'])
            },
            'respiratoryRate': round(vitals['respiratoryRate']),
            'glucose': round(vitals['glucose']),
            'bedOccupancy': True,
            'patientId': patient_id,
            'deviceStatus': 'online',
            'batteryLevel': 85 + random.randint(0, 14),
            'signalStrength': 85 + random.randint(0, 14)
        }
    
    def post_vitals_to_db(self, device_id: str, vitals_data: Dict) -> bool:
        """Post vitals data to Firebase"""
        try:
            # Get current timestamp
            timestamp = self.sanitize_timestamp(datetime.now().isoformat())
            
            # Update vitals in Firebase
            vitals_ref = db.reference(f'iotData/{device_id}/vitals')
            vitals_ref.child(timestamp).set(vitals_data)
            
            logger.info(f"✓ Successfully posted vitals for {device_id}")
            return True
                
        except Exception as e:
            logger.error(f"✗ Error posting vitals for {device_id}: {str(e)}")
            return False

    def simulate_patient_monitor(self, patient_id: str, device_id: str, interval: int = 5):
        """Simulate a single patient monitor"""
        logger.info(f"Starting simulation for {patient_id} on device {device_id}")
        
        while self.running:
            try:
                # Generate vitals
                vitals_data = self.generate_patient_vitals(patient_id)
                
                if vitals_data:
                    # Post to Firebase
                    success = self.post_vitals_to_db(device_id, vitals_data)
                    
                    if success:
                        logger.info(f"Monitor {device_id} - HR: {vitals_data['heartRate']}, "
                                  f"O2: {vitals_data['oxygenLevel']}%, "
                                  f"Temp: {vitals_data['temperature']}°C, "
                                  f"BP: {vitals_data['bloodPressure']['systolic']}/{vitals_data['bloodPressure']['diastolic']}")
                else:
                    logger.warning(f"Failed to generate vitals for {patient_id}")
                
                # Wait for next interval
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in simulation for {patient_id}: {str(e)}")
                time.sleep(interval)

    def start_simulation(self, interval: int = 5):
        """Start simulation for all active monitors"""
        logger.info("Starting vitals simulation...")
        
        # First, fetch monitor and patient data
        if not self.fetch_monitor_data():
            logger.error("Failed to fetch monitor data. Cannot start simulation.")
            return False
        
        if not self.monitors:
            logger.error("No active monitors found. Cannot start simulation.")
            return False
        
        self.running = True
        
        # Create a thread for each active monitor
        for monitor_id, monitor_info in self.monitors.items():
            patient_id = monitor_info['patientId']
            if patient_id in self.patients:  # Only simulate if we have patient data
                thread = threading.Thread(
                    target=self.simulate_patient_monitor,
                    args=(patient_id, monitor_id, interval),
                    daemon=True
                )
                thread.start()
                self.simulation_threads.append(thread)
                logger.info(f"Started simulation for monitor {monitor_id} (Patient: {patient_id})")
            else:
                logger.warning(f"Skipping monitor {monitor_id} - no patient data available")
        
        logger.info(f"Started {len(self.simulation_threads)} monitor simulations")
        return True

    def stop_simulation(self):
        """Stop the simulation"""
        logger.info("Stopping vitals simulation...")
        self.running = False
        
        # Wait for all threads to finish
        for thread in self.simulation_threads:
            thread.join(timeout=1)
        
        self.simulation_threads.clear()
        logger.info("Simulation stopped")

    def run_simulation(self, duration: Optional[int] = None, interval: int = 5):
        """Run simulation for a specified duration or indefinitely"""
        try:
            if not self.start_simulation(interval):
                return
            
            if duration:
                logger.info(f"Running simulation for {duration} seconds...")
                time.sleep(duration)
                self.stop_simulation()
            else:
                logger.info("Running simulation indefinitely. Press Ctrl+C to stop...")
                while self.running:
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            logger.info("Received interrupt signal...")
            self.stop_simulation()
        except Exception as e:
            logger.error(f"Unexpected error in simulation: {str(e)}")
            self.stop_simulation() 