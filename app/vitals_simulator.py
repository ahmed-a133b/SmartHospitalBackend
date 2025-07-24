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
        self.environmental_sensors = {}  # Will store environmental sensors by room
        self.patients = {}  # Will store patient data
        self.patient_vitals_cache = {}  # Cache for current vital values
        self.environmental_cache = {}  # Cache for current environmental values
        
    def fetch_monitor_data(self) -> bool:
        """Fetch monitor data and their assigned patients from Firebase"""
        try:
            iot_ref = db.reference('iotData')
            monitors_data = iot_ref.get()
            
            if monitors_data:
                logger.info(f"Successfully fetched {len(monitors_data)} devices from database")
                
                # Process different types of devices
                for device_id, device_data in monitors_data.items():
                    device_info = device_data.get('deviceInfo', {})
                    device_type = device_info.get('type', '')
                    
                    # Get the latest vitals entry if it exists
                    vitals = device_data.get('vitals', {})
                    latest_vitals = None
                    if vitals:
                        # Check if vitals are organized by patient (new structure)
                        if any(isinstance(v, dict) and not any(key in v for key in ['heartRate', 'humidity']) for v in vitals.values()):
                            # Patient-organized structure: get latest from all patients
                            all_vitals = []
                            for patient_vitals in vitals.values():
                                if isinstance(patient_vitals, dict):
                                    for timestamp, vital_data in patient_vitals.items():
                                        all_vitals.append((timestamp, vital_data))
                            if all_vitals:
                                # Sort and get latest
                                latest_timestamp = max(all_vitals, key=lambda x: x[0])[0]
                                latest_vitals = max(all_vitals, key=lambda x: x[0])[1]
                        else:
                            # Old structure: get latest timestamp's data
                            latest_timestamp = max(vitals.keys())
                            latest_vitals = vitals[latest_timestamp]
                    
                    if device_type == 'vitals_monitor':
                        # Handle patient vitals monitors
                        patient_id = None
                        
                        # Try to get patient ID from device info first (new structure)
                        if 'currentPatientId' in device_info:
                            patient_id = device_info['currentPatientId']
                        # Fallback to checking latest vitals for backwards compatibility
                        elif latest_vitals and 'patientId' in latest_vitals:
                            patient_id = latest_vitals['patientId']
                        
                        if patient_id:
                            self.monitors[device_id] = {
                                'patientId': patient_id,
                                'deviceInfo': device_info,
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
                    
                    elif device_type == 'environmental_sensor':
                        # Handle environmental sensors
                        room_id = device_info.get('roomId')
                        if room_id:
                            self.environmental_sensors[device_id] = {
                                'roomId': room_id,
                                'deviceInfo': device_info,
                                'lastReading': latest_vitals
                            }
                            
                            # Initialize environmental cache
                            if latest_vitals:
                                self.environmental_cache[device_id] = self.convert_environmental_to_cache_format(latest_vitals)
                            else:
                                self.environmental_cache[device_id] = self.get_initial_environmental_data(room_id)
                
                logger.info(f"Found {len(self.monitors)} patient monitors and {len(self.environmental_sensors)} environmental sensors")
                return bool(self.monitors) or bool(self.environmental_sensors)
            else:
                logger.error("No devices found in database")
                return False
                
        except Exception as e:
            logger.error(f"Error fetching device data: {str(e)}")
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
    
    def convert_environmental_to_cache_format(self, environmental_data: Dict) -> Dict:
        """Convert environmental data from Firebase format to cache format"""
        return {
            'temperature': environmental_data.get('temperature', 22.0),
            'humidity': environmental_data.get('humidity', 45),
            'airQuality': environmental_data.get('airQuality', 95),
            'lightLevel': environmental_data.get('lightLevel', 80),
            'noiseLevel': environmental_data.get('noiseLevel', 35),
            'pressure': environmental_data.get('pressure', 1013.25),
            'co2Level': environmental_data.get('co2Level', 400)
        }
    
    def get_initial_environmental_data(self, room_id: str) -> Dict:
        """Get initial environmental data for a room"""
        # Different room types have different baseline environmental conditions
        room_baselines = {
            'ICU': {
                'temperature': 22.0,
                'humidity': 45,
                'airQuality': 95,
                'lightLevel': 75,
                'noiseLevel': 40,
                'pressure': 1013.25,
                'co2Level': 400
            },
            'isolation': {
                'temperature': 23.0,
                'humidity': 50,
                'airQuality': 98,
                'lightLevel': 70,
                'noiseLevel': 30,
                'pressure': 1013.30,
                'co2Level': 380
            },
            'general': {
                'temperature': 21.5,
                'humidity': 55,
                'airQuality': 92,
                'lightLevel': 85,
                'noiseLevel': 45,
                'pressure': 1013.15,
                'co2Level': 420
            }
        }
        
        # Try to get room type from room_id or use general as default
        room_type = 'general'  # Default
        if 'icu' in room_id.lower():
            room_type = 'ICU'
        elif 'isolation' in room_id.lower():
            room_type = 'isolation'
        
        baseline = room_baselines.get(room_type, room_baselines['general'])
        
        # Add some initial variation
        return {
            'temperature': baseline['temperature'] + random.uniform(-1.0, 1.0),
            'humidity': baseline['humidity'] + random.randint(-5, 5),
            'airQuality': baseline['airQuality'] + random.randint(-3, 3),
            'lightLevel': baseline['lightLevel'] + random.randint(-10, 10),
            'noiseLevel': baseline['noiseLevel'] + random.randint(-5, 5),
            'pressure': baseline['pressure'] + random.uniform(-0.5, 0.5),
            'co2Level': baseline['co2Level'] + random.randint(-20, 20)
        }
    
    def generate_environmental_data(self, device_id: str) -> Optional[Dict]:
        """Generate realistic environmental data for a room sensor"""
        try:
            if device_id not in self.environmental_sensors:
                return None
            
            sensor_info = self.environmental_sensors[device_id]
            room_id = sensor_info['roomId']
            
            # Initialize cache if not exists
            if device_id not in self.environmental_cache:
                self.environmental_cache[device_id] = self.get_initial_environmental_data(room_id)
            
            current_env = self.environmental_cache[device_id]
            
            # Get current time for circadian effects
            hour = datetime.now().hour
            
            # Generate new environmental values with realistic variations
            env_data = dict(current_env)
            
            # Temperature variations based on time of day and HVAC cycles
            temp_circadian = math.sin((hour - 6) * math.pi / 12) * 1.5  # Peak at 6 PM
            env_data['temperature'] += temp_circadian + random.uniform(-0.3, 0.3)
            
            # Humidity varies inversely with temperature and has HVAC effects
            humidity_change = random.uniform(-2, 2)
            if env_data['temperature'] > current_env['temperature']:
                humidity_change -= 1  # Temperature up, humidity tends down
            env_data['humidity'] += humidity_change
            
            # Air quality affected by occupancy and ventilation
            # Assume lower quality during busy hours (8 AM - 8 PM)
            if 8 <= hour <= 20:
                env_data['airQuality'] += random.uniform(-2, 1)
            else:
                env_data['airQuality'] += random.uniform(-0.5, 2)
            
            # Light level varies with time of day
            if 6 <= hour <= 22:  # Daytime/evening
                target_light = 80 + (22 - abs(hour - 14)) * 2  # Peak at 2 PM
            else:  # Nighttime
                target_light = 20
            
            light_diff = target_light - env_data['lightLevel']
            env_data['lightLevel'] += light_diff * 0.3 + random.uniform(-5, 5)
            
            # Noise level varies with hospital activity
            if 6 <= hour <= 22:  # Active hours
                env_data['noiseLevel'] += random.uniform(-3, 8)
            else:  # Quiet hours
                env_data['noiseLevel'] += random.uniform(-5, 2)
            
            # Atmospheric pressure (minor variations)
            env_data['pressure'] += random.uniform(-0.1, 0.1)
            
            # CO2 level affected by occupancy and ventilation
            if 8 <= hour <= 20:  # Busier times
                env_data['co2Level'] += random.uniform(-5, 15)
            else:
                env_data['co2Level'] += random.uniform(-10, 5)
            
            # Apply realistic bounds
            env_data['temperature'] = max(18, min(28, env_data['temperature']))
            env_data['humidity'] = max(30, min(70, env_data['humidity']))
            env_data['airQuality'] = max(70, min(100, env_data['airQuality']))
            env_data['lightLevel'] = max(0, min(100, env_data['lightLevel']))
            env_data['noiseLevel'] = max(20, min(80, env_data['noiseLevel']))
            env_data['pressure'] = max(1010, min(1020, env_data['pressure']))
            env_data['co2Level'] = max(350, min(800, env_data['co2Level']))
            
            # Update cache
            self.environmental_cache[device_id] = env_data
            
            return {
                'temperature': round(env_data['temperature'] * 10) / 10,
                'humidity': round(env_data['humidity']),
                'airQuality': round(env_data['airQuality']),
                'lightLevel': round(env_data['lightLevel']),
                'noiseLevel': round(env_data['noiseLevel']),
                'pressure': round(env_data['pressure'] * 100) / 100,
                'co2Level': round(env_data['co2Level']),
                'deviceStatus': 'online',
                'batteryLevel': 80 + random.randint(0, 19),
                'signalStrength': 85 + random.randint(0, 14)
            }
            
        except Exception as e:
            logger.error(f"Error generating environmental data for {device_id}: {str(e)}")
            return None
    
    def post_vitals_to_db(self, device_id: str, vitals_data: Dict) -> bool:
        """Post vitals data to Firebase with patient-based organization"""
        try:
            # Get current timestamp
            timestamp = self.sanitize_timestamp(datetime.now().isoformat())
            
            # Get patient ID from vitals data
            patient_id = vitals_data.get('patientId')
            if not patient_id:
                logger.error(f"No patient ID found in vitals data for device {device_id}")
                return False
            
            # Verify that this patient is actually assigned to the device
            device_ref = db.reference(f'iotData/{device_id}/deviceInfo')
            device_info = device_ref.get()
            
            if not device_info or device_info.get('currentPatientId') != patient_id:
                logger.warning(f"Patient {patient_id} is not currently assigned to device {device_id}. Skipping vitals storage.")
                return False
            
            # Store vitals using the new structure: vitals[patient_id][timestamp] = vital_record
            vitals_ref = db.reference(f'iotData/{device_id}/vitals/{patient_id}/{timestamp}')
            vitals_ref.set(vitals_data)
            
            logger.info(f"✓ Successfully posted vitals for {device_id} (Patient: {patient_id})")
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

    def simulate_environmental_sensor(self, device_id: str, interval: int = 15):
        """Simulate a single environmental sensor"""
        sensor_info = self.environmental_sensors[device_id]
        room_id = sensor_info['roomId']
        logger.info(f"Starting environmental simulation for {device_id} in {room_id}")
        
        while self.running:
            try:
                # Generate environmental data
                env_data = self.generate_environmental_data(device_id)
                
                if env_data:
                    # Post to Firebase
                    success = self.post_vitals_to_db(device_id, env_data)
                    
                    if success:
                        logger.info(f"Environmental {device_id} - Temp: {env_data['temperature']}°C, "
                                  f"Humidity: {env_data['humidity']}%, "
                                  f"Air Quality: {env_data['airQuality']}, "
                                  f"CO2: {env_data['co2Level']} ppm")
                else:
                    logger.warning(f"Failed to generate environmental data for {device_id}")
                
                # Wait for next interval (environmental sensors update less frequently)
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in environmental simulation for {device_id}: {str(e)}")
                time.sleep(interval)

    def start_simulation(self, interval: int = 5):
        """Start simulation for all active monitors and environmental sensors"""
        logger.info("Starting vitals and environmental simulation...")
        
        # First, fetch monitor and patient data
        if not self.fetch_monitor_data():
            logger.error("Failed to fetch device data. Cannot start simulation.")
            return False
        
        if not self.monitors and not self.environmental_sensors:
            logger.error("No active devices found. Cannot start simulation.")
            return False
        
        self.running = True
        
        # Create threads for patient monitors
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
        
        # Create threads for environmental sensors
        for sensor_id, sensor_info in self.environmental_sensors.items():
            room_id = sensor_info['roomId']
            thread = threading.Thread(
                target=self.simulate_environmental_sensor,
                args=(sensor_id, interval * 3),  # Environmental sensors update less frequently
                daemon=True
            )
            thread.start()
            self.simulation_threads.append(thread)
            logger.info(f"Started environmental simulation for sensor {sensor_id} (Room: {room_id})")
        
        logger.info(f"Started {len(self.simulation_threads)} simulations ({len(self.monitors)} monitors, {len(self.environmental_sensors)} environmental sensors)")
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