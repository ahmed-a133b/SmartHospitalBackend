import os
import json
import time
import random
import signal
import sys
import math
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import threading
import logging
from dataclasses import dataclass, asdict
from enum import Enum
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db

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

class PatientState(Enum):
    STABLE = "stable"
    DETERIORATING = "deteriorating"
    CRITICAL = "critical"
    RECOVERING = "recovering"
    AT_RISK = "at_risk"

class RiskScenario(Enum):
    CARDIAC_STRESS = "cardiac_stress"
    HYPERTENSIVE_PATTERN = "hypertensive_pattern"
    HYPOTENSIVE_TREND = "hypotensive_trend"
    RESPIRATORY_COMPROMISE = "respiratory_compromise"
    OXYGEN_DESATURATION = "oxygen_desaturation"
    FEVER_PROGRESSION = "fever_progression"
    HYPOTHERMIC_TREND = "hypothermic_trend"
    GLYCEMIC_INSTABILITY = "glycemic_instability"
    TACHYCARDIC_PATTERN = "tachycardic_pattern"
    BRADYCARDIC_PATTERN = "bradycardic_pattern"

@dataclass
class PatientProfile:
    patientId: str
    age: int
    conditions: List[str]
    medications: List[str]
    riskFactors: List[str]
    baselineVitals: Dict
    currentState: str  # stable, deteriorating, critical, recovering, at_risk
    scenario: Optional[str] = None  # Current risk scenario if any
    scenario_start_time: Optional[datetime] = None
    scenario_progression: float = 0.0  # 0.0 to 1.0, tracks scenario development

class VitalPatternGenerator:
    """Generates realistic vital sign patterns that may indicate health risks"""
    
    def __init__(self):
        self.active_scenarios = {}  # deviceId -> scenario info
        self.scenario_probabilities = {
            RiskScenario.CARDIAC_STRESS: 0.15,
            RiskScenario.HYPERTENSIVE_PATTERN: 0.12,
            RiskScenario.HYPOTENSIVE_TREND: 0.10,
            RiskScenario.RESPIRATORY_COMPROMISE: 0.12,
            RiskScenario.OXYGEN_DESATURATION: 0.10,
            RiskScenario.FEVER_PROGRESSION: 0.18,
            RiskScenario.HYPOTHERMIC_TREND: 0.08,
            RiskScenario.GLYCEMIC_INSTABILITY: 0.15,
            RiskScenario.TACHYCARDIC_PATTERN: 0.12,
            RiskScenario.BRADYCARDIC_PATTERN: 0.10,
        }
    
    def should_start_risk_scenario(self, patient_profile: PatientProfile) -> Optional[RiskScenario]:
        """Determine if a risk scenario should begin based on patient characteristics"""
        # Don't start new scenario if one is already active
        if patient_profile.scenario:
            return None
            
        # Adjust probabilities based on patient conditions and risk factors
        adjusted_probabilities = self.scenario_probabilities.copy()
        
        if 'heart_disease' in patient_profile.conditions or 'cardiac_risk' in patient_profile.riskFactors:
            adjusted_probabilities[RiskScenario.CARDIAC_STRESS] *= 3
            adjusted_probabilities[RiskScenario.TACHYCARDIC_PATTERN] *= 2
            adjusted_probabilities[RiskScenario.BRADYCARDIC_PATTERN] *= 2
        
        if 'hypertension' in patient_profile.conditions:
            adjusted_probabilities[RiskScenario.HYPERTENSIVE_PATTERN] *= 4
        
        if 'diabetes' in patient_profile.conditions or 'diabetic_risk' in patient_profile.riskFactors:
            adjusted_probabilities[RiskScenario.GLYCEMIC_INSTABILITY] *= 4
        
        if any(cond in patient_profile.conditions for cond in ['copd', 'asthma']) or 'respiratory_risk' in patient_profile.riskFactors:
            adjusted_probabilities[RiskScenario.RESPIRATORY_COMPROMISE] *= 3
            adjusted_probabilities[RiskScenario.OXYGEN_DESATURATION] *= 3
        
        # Age-based risk adjustments
        if patient_profile.age > 70:
            for scenario in adjusted_probabilities:
                adjusted_probabilities[scenario] *= 1.5
        elif patient_profile.age < 18:
            # Pediatric patients have different risk patterns
            adjusted_probabilities[RiskScenario.FEVER_PROGRESSION] *= 2
            adjusted_probabilities[RiskScenario.RESPIRATORY_COMPROMISE] *= 1.5
        
        # Current state affects likelihood
        if patient_profile.currentState == 'critical':
            for scenario in adjusted_probabilities:
                adjusted_probabilities[scenario] *= 2
        elif patient_profile.currentState == 'at_risk':
            for scenario in adjusted_probabilities:
                adjusted_probabilities[scenario] *= 1.5
        
        # Check for scenario trigger
        for scenario, probability in adjusted_probabilities.items():
            if random.random() < probability:
                return scenario
        
        return None
    
    def generate_scenario_vitals(self, scenario: RiskScenario, baseline_vitals: Dict, 
                               progression: float, time_elapsed: int) -> Dict:
        """Generate vitals for a specific risk scenario based on progression (0.0-1.0)"""
        vitals = baseline_vitals.copy()
        
        # Use sine wave and other mathematical functions for realistic progression
        wave_factor = math.sin(time_elapsed * 0.2) * 0.5  # Adds natural variation with more amplitude
        trend_factor = 1 + (progression * 0.3)  # Increases effect as scenario progresses
        
        if scenario == RiskScenario.CARDIAC_STRESS:
            # Gradual increase in heart rate with increasing variability
            hr_increase = int(progression * 60 + wave_factor * 15)
            vitals['heartRate'] = baseline_vitals['heartRate'] + hr_increase
            # Slight blood pressure changes
            vitals['systolicBP'] = baseline_vitals['systolicBP'] + int(progression * 30 + wave_factor * 8)
            vitals['diastolicBP'] = baseline_vitals['diastolicBP'] + int(progression * 15 + wave_factor * 5)
            
        elif scenario == RiskScenario.HYPERTENSIVE_PATTERN:
            # Progressive increase in blood pressure
            systolic_increase = int(progression * 70 + wave_factor * 10)
            diastolic_increase = int(progression * 35 + wave_factor * 8)
            vitals['systolicBP'] = baseline_vitals['systolicBP'] + systolic_increase
            vitals['diastolicBP'] = baseline_vitals['diastolicBP'] + diastolic_increase
            # Compensatory heart rate changes
            vitals['heartRate'] = baseline_vitals['heartRate'] + int(progression * 25 + wave_factor * 5)
            
        elif scenario == RiskScenario.HYPOTENSIVE_TREND:
            # Gradual decrease in blood pressure
            systolic_decrease = int(progression * 45 + wave_factor * 8)
            diastolic_decrease = int(progression * 25 + wave_factor * 5)
            vitals['systolicBP'] = max(70, baseline_vitals['systolicBP'] - systolic_decrease)
            vitals['diastolicBP'] = max(40, baseline_vitals['diastolicBP'] - diastolic_decrease)
            # Compensatory tachycardia
            vitals['heartRate'] = baseline_vitals['heartRate'] + int(progression * 35 + wave_factor * 8)
            
        elif scenario == RiskScenario.RESPIRATORY_COMPROMISE:
            # Increasing respiratory rate with declining efficiency
            rr_increase = int(progression * 18 + wave_factor * 4)
            vitals['respiratoryRate'] = baseline_vitals['respiratoryRate'] + rr_increase
            # Gradual oxygen decline
            o2_decline = progression * 12 + wave_factor * 3
            vitals['oxygenLevel'] = max(80, baseline_vitals['oxygenLevel'] - o2_decline)
            # Heart rate compensation
            vitals['heartRate'] = baseline_vitals['heartRate'] + int(progression * 30 + wave_factor * 8)
            
        elif scenario == RiskScenario.OXYGEN_DESATURATION:
            # Progressive oxygen desaturation
            o2_decline = progression * 18 + wave_factor * 4
            vitals['oxygenLevel'] = max(75, baseline_vitals['oxygenLevel'] - o2_decline)
            # Respiratory compensation
            vitals['respiratoryRate'] = baseline_vitals['respiratoryRate'] + int(progression * 12 + wave_factor * 3)
            vitals['heartRate'] = baseline_vitals['heartRate'] + int(progression * 25 + wave_factor * 6)
            
        elif scenario == RiskScenario.FEVER_PROGRESSION:
            # Gradual temperature rise
            temp_increase = progression * 3.5 + wave_factor * 0.4
            vitals['temperature'] = baseline_vitals['temperature'] + temp_increase
            # Physiological responses to fever
            vitals['heartRate'] = baseline_vitals['heartRate'] + int(progression * 35 + wave_factor * 8)
            vitals['respiratoryRate'] = baseline_vitals['respiratoryRate'] + int(progression * 10 + wave_factor * 2)
            
        elif scenario == RiskScenario.HYPOTHERMIC_TREND:
            # Gradual temperature drop
            temp_decrease = progression * 4.0 + wave_factor * 0.5
            vitals['temperature'] = max(33.0, baseline_vitals['temperature'] - temp_decrease)
            # Physiological responses to hypothermia
            vitals['heartRate'] = max(40, baseline_vitals['heartRate'] - int(progression * 30 + wave_factor * 5))
            vitals['respiratoryRate'] = max(8, baseline_vitals['respiratoryRate'] - int(progression * 6 + wave_factor * 2))
            
        elif scenario == RiskScenario.GLYCEMIC_INSTABILITY:
            # Fluctuating glucose levels with larger swings
            if random.choice([True, False]):  # Hyperglycemia
                glucose_increase = progression * 200 + wave_factor * 40
                vitals['glucose'] = baseline_vitals['glucose'] + glucose_increase
            else:  # Hypoglycemia
                glucose_decrease = progression * 60 + wave_factor * 15
                vitals['glucose'] = max(50, baseline_vitals['glucose'] - glucose_decrease)
            
        elif scenario == RiskScenario.TACHYCARDIC_PATTERN:
            # Progressive tachycardia
            hr_increase = int(progression * 70 + wave_factor * 12)
            vitals['heartRate'] = min(190, baseline_vitals['heartRate'] + hr_increase)
            
        elif scenario == RiskScenario.BRADYCARDIC_PATTERN:
            # Progressive bradycardia
            hr_decrease = int(progression * 40 + wave_factor * 8)
            vitals['heartRate'] = max(35, baseline_vitals['heartRate'] - hr_decrease)
        
        # Ensure all vitals stay within realistic bounds
        vitals['heartRate'] = max(30, min(200, vitals['heartRate']))
        vitals['oxygenLevel'] = max(70, min(100, vitals['oxygenLevel']))
        vitals['temperature'] = max(32.0, min(42.0, vitals['temperature']))
        vitals['systolicBP'] = max(60, min(220, vitals['systolicBP']))
        vitals['diastolicBP'] = max(40, min(130, vitals['diastolicBP']))
        vitals['respiratoryRate'] = max(8, min(40, vitals['respiratoryRate']))
        vitals['glucose'] = max(40, min(500, vitals['glucose']))
        
        return vitals

class EnvironmentalDataGenerator:
    """Generates realistic environmental data without hazards"""
    
    def __init__(self):
        pass
    
    def generate_environmental_data(self, room_type: str, baseline: Optional[Dict] = None) -> Dict:
        """Generate normal environmental data with natural variation"""
        if baseline is None:
            baseline = {
                'temperature': 22.0,
                'humidity': 45.0,
                'airQuality': 85.0,
                'noiseLevel': 35.0,
                'co2Level': 400.0,
                'lightLevel': 300.0
            }
        
        # Add natural variation with larger ranges for more noticeable changes
        env_data = {
            'temperature': baseline['temperature'] + random.uniform(-2.5, 2.5),
            'humidity': max(25, min(80, baseline['humidity'] + random.uniform(-10, 15))),
            'airQuality': max(40, min(100, baseline['airQuality'] + random.uniform(-15, 10))),
            'noiseLevel': max(20, baseline['noiseLevel'] + random.uniform(-10, 20)),
            'co2Level': max(300, baseline['co2Level'] + random.uniform(-100, 200)),
            'lightLevel': max(150, baseline['lightLevel'] + random.uniform(-100, 150)),
            'pressure': 1013.25 + random.uniform(-5, 5)  # Add atmospheric pressure
        }
        
        return env_data

class AnomalyDetectionService:
    """Service to continuously monitor patients using the anomaly detection API"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.last_check_times = {}  # Track last check time for each patient
        self.detected_anomalies = {}  # Store detected anomalies
        
    def check_patient_anomalies(self, patient_id: str, monitor_id: str) -> Optional[Dict]:
        """Check for anomalies for a specific patient using monitor ID"""
        try:
            # Call the correct anomaly detection endpoint
            response = requests.get(
                f"{self.api_base_url}/anomalies/detect/{monitor_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if any anomalies were detected using correct API response format
                if result.get('is_anomaly'):
                    anomaly_types = result.get('anomaly_type', [])
                    severity = result.get('severity_level', 'UNKNOWN')
                    confidence = result.get('confidence', 0.0)
                    anomaly_score = result.get('anomaly_score', 0.0)
                    
                    logger.warning(f"🚨 ANOMALIES DETECTED for patient {patient_id}: {len(anomaly_types)} anomaly types")
                    
                    # Log anomaly details
                    for anomaly_type in anomaly_types:
                        logger.warning(f"📊 {anomaly_type}")
                    logger.warning(f"🔴 Severity: {severity} | Confidence: {confidence:.2f}")
                    logger.warning(f"📈 Anomaly Score: {anomaly_score:.3f}")
                    
                    return result
                else:
                    logger.debug(f"✅ No anomalies detected for patient {patient_id}")
                    return None
                    
            else:
                logger.error(f"❌ Failed to check anomalies for patient {patient_id} (monitor {monitor_id}): HTTP {response.status_code}")
                logger.error(f"Response: {response.text if response.text else 'No response body'}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error calling anomaly detection API for patient {patient_id} (monitor {monitor_id}): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error checking anomalies for patient {patient_id}: {str(e)}")
            return None
    
   
    
    def map_severity_to_alert_type(self, severity: str) -> str:
        """Map anomaly severity to alert type"""
        severity_map = {
            'low': 'info',
            'medium': 'warning',
            'high': 'warning',
            'critical': 'critical'
        }
        return severity_map.get(severity.lower(), 'warning')
    
    def check_all_patients(self, patient_profiles: Dict) -> Dict[str, Optional[Dict]]:
        """Check anomalies for all patients"""
        results = {}
        
        for monitor_id, patient_profile in patient_profiles.items():
            patient_id = patient_profile.patientId
            
            # Check if enough time has passed since last check (avoid spam)
            last_check = self.last_check_times.get(patient_id)
            current_time = datetime.now()
            
            if last_check is None or (current_time - last_check).total_seconds() >= 30:  # Check every 30 seconds
                result = self.check_patient_anomalies(patient_id, monitor_id)
                results[patient_id] = result
                self.last_check_times[patient_id] = current_time
            else:
                results[patient_id] = None  # Skipped due to rate limiting
                
        return results
    
    def get_anomaly_summary(self) -> Dict:
        """Get summary of detected anomalies"""
        total_patients_with_anomalies = len(self.detected_anomalies)
        total_anomalies = sum(data['total_count'] for data in self.detected_anomalies.values())
        
        recent_anomalies = []
        cutoff_time = datetime.now() - timedelta(minutes=10)
        
        for patient_id, data in self.detected_anomalies.items():
            if data['timestamp'] > cutoff_time:
                recent_anomalies.append({
                    'patient_id': patient_id,
                    'timestamp': data['timestamp'],
                    'count': data['total_count']
                })
        
        return {
            'total_patients_with_anomalies': total_patients_with_anomalies,
            'total_anomalies_detected': total_anomalies,
            'recent_anomalies_count': len(recent_anomalies),
            'recent_anomalies': recent_anomalies
        }

def format_datetime_for_firebase(dt):
    """Format datetime in a Firebase-safe format"""
    return dt.strftime("%Y-%m-%d_%H-%M-%S")

class EnhancedHospitalDataSimulator:
    def __init__(self):
        self.init_firebase()
        self.vital_pattern_generator = VitalPatternGenerator()
        self.env_data_generator = EnvironmentalDataGenerator()
        self.anomaly_detector = AnomalyDetectionService()
        self.patient_profiles = {}
        self.environmental_sensors = {}
        self.simulation_cycle = 0
        
    def init_firebase(self):
        """Initialize Firebase connection"""
        logger.info("Initializing Firebase connection...")
        load_dotenv()
        json_str = os.getenv("FIREBASE_KEY_JSON")
        db_url = os.getenv("FIREBASE_DATABASE_URL")

        if not json_str or not db_url:
            logger.error("Missing FIREBASE_KEY_JSON or FIREBASE_DATABASE_URL environment variables")
            raise ValueError("Missing FIREBASE_KEY_JSON or FIREBASE_DATABASE_URL")

        try:
            json_data = json.loads(json_str)  
            cred = credentials.Certificate(json_data)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred, {
                    'databaseURL': db_url
                })
                logger.info("Firebase initialized successfully")
            else:
                logger.info("Firebase already initialized")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid FIREBASE_KEY_JSON: {str(e)}")
            raise ValueError("Invalid FIREBASE_KEY_JSON") from e
        except Exception as e:
            logger.error(f"Error initializing Firebase: {str(e)}")
            raise
    
    def load_patient_profiles(self):
        """Load patient data and create profiles for simulation"""
        try:
            logger.info("Starting to load patient profiles...")
            # Get monitors and their assigned patients
            iot_ref = db.reference('iotData')
            monitors_data = iot_ref.get()
            
            if not monitors_data:
                logger.warning("No IoT monitors found in Firebase")
                return
            
            logger.info(f"Found {len(monitors_data)} monitors in Firebase")
            
            # Get patient data
            patients_ref = db.reference('patients')
            patients_data = patients_ref.get() or {}
            
            logger.info(f"Found {len(patients_data)} patients in Firebase")
            
            for monitor_id, monitor_data in monitors_data.items():
                device_info = monitor_data.get('deviceInfo', {})
                logger.info(f"Processing monitor {monitor_id} with device type: {device_info.get('type', 'unknown')}")
                
                if device_info.get('type') == 'vitals_monitor':
                    # Get patient ID from latest vitals or device info
                    patient_id = device_info.get('currentPatientId')
                    logger.info(f"Monitor {monitor_id} has currentPatientId: {patient_id}")
                    
                    if not patient_id:
                        # Try to get from latest vitals - check if we have vitals organized by patient
                        vitals = monitor_data.get('vitals', {})
                        if vitals:
                            # With new structure, vitals are organized as vitals[patient_id][timestamp]
                            # Get the most recent patient that has vitals
                            for potential_patient_id, patient_vitals in vitals.items():
                                if patient_vitals:  # This patient has vitals data
                                    patient_id = potential_patient_id
                                    logger.info(f"Found patient ID from vitals: {patient_id}")
                                    break
                    
                    if patient_id and patient_id in patients_data:
                        patient_data = patients_data[patient_id]
                        personal_info = patient_data.get('personalInfo', {})
                        medical_history = patient_data.get('medicalHistory', {})
                        current_status = patient_data.get('currentStatus', {})
                        
                        # Create patient profile
                        profile = PatientProfile(
                            patientId=patient_id,
                            age=personal_info.get('age', 50),
                            conditions=[cond.lower() for cond in medical_history.get('conditions', [])],
                            medications=[med.get('name', '') for med in medical_history.get('medications', [])],
                            riskFactors=self.determine_risk_factors(personal_info, medical_history),
                            baselineVitals=self.calculate_baseline_vitals(personal_info, medical_history),
                            currentState=current_status.get('status', 'stable').lower()
                        )
                        
                        self.patient_profiles[monitor_id] = profile
                        logger.info(f"Successfully loaded profile for patient {patient_id} on monitor {monitor_id}")
                    else:
                        logger.warning(f"No patient found for monitor {monitor_id} (patient_id: {patient_id})")
                
                elif device_info.get('type') == 'environmental_sensor':
                    # Store environmental sensor info
                    self.environmental_sensors[monitor_id] = {
                        'roomId': device_info.get('roomId'),
                        'roomType': device_info.get('roomType', 'general_ward'),
                        'deviceInfo': device_info
                    }
                    logger.info(f"Loaded environmental sensor {monitor_id}")
            
            logger.info(f"Loaded {len(self.patient_profiles)} patient profiles and {len(self.environmental_sensors)} environmental sensors")
            
        except Exception as e:
            logger.error(f"Error loading patient profiles: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def determine_risk_factors(self, personal_info: Dict, medical_history: Dict) -> List[str]:
        """Determine risk factors based on patient information"""
        risk_factors = []
        
        age = personal_info.get('age', 0)
        if age > 65:
            risk_factors.append('elderly')
        if age < 18:
            risk_factors.append('pediatric')
        
        conditions = [cond.lower() for cond in medical_history.get('conditions', [])]
        
        if any(cond in conditions for cond in ['heart_disease', 'cardiac', 'hypertension']):
            risk_factors.append('cardiac_risk')
        if any(cond in conditions for cond in ['diabetes', 'diabetic']):
            risk_factors.append('diabetic_risk')
        if any(cond in conditions for cond in ['copd', 'asthma', 'respiratory']):
            risk_factors.append('respiratory_risk')
        if any(cond in conditions for cond in ['kidney', 'renal']):
            risk_factors.append('renal_risk')
        
        medications = [med.get('name', '').lower() for med in medical_history.get('medications', [])]
        if any('warfarin' in med or 'heparin' in med for med in medications):
            risk_factors.append('bleeding_risk')
        if any('insulin' in med for med in medications):
            risk_factors.append('hypoglycemia_risk')
        
        return risk_factors
    
    def calculate_baseline_vitals(self, personal_info: Dict, medical_history: Dict) -> Dict:
        """Calculate baseline vitals based on patient characteristics"""
        age = personal_info.get('age', 50)
        conditions = [cond.lower() for cond in medical_history.get('conditions', [])]
        
        # Age-based baselines
        if age < 18:
            baseline = {'heartRate': 90, 'systolicBP': 105, 'diastolicBP': 65, 'respiratoryRate': 20}
        elif age < 65:
            baseline = {'heartRate': 70, 'systolicBP': 120, 'diastolicBP': 80, 'respiratoryRate': 16}
        else:
            baseline = {'heartRate': 75, 'systolicBP': 130, 'diastolicBP': 85, 'respiratoryRate': 18}
        
        # Common baselines
        baseline.update({
            'oxygenLevel': 98,
            'temperature': 37.0,
            'glucose': 100
        })
        
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
        
        return baseline
    
    def generate_normal_vitals(self, baseline: Dict, variation_factor: float = 1.0) -> Dict:
        """Generate normal vitals with natural variation"""
        vitals = {}
        
        # Add realistic variation to each vital sign with increased ranges
        vitals['heartRate'] = max(50, min(120, baseline['heartRate'] + random.randint(-15, 15) * variation_factor))
        vitals['oxygenLevel'] = max(90, min(100, baseline['oxygenLevel'] + random.uniform(-3, 2) * variation_factor))
        vitals['temperature'] = max(35.5, min(39.0, baseline['temperature'] + random.uniform(-0.8, 0.8) * variation_factor))
        vitals['systolicBP'] = max(80, min(160, baseline['systolicBP'] + random.randint(-20, 20) * variation_factor))
        vitals['diastolicBP'] = max(50, min(100, baseline['diastolicBP'] + random.randint(-15, 15) * variation_factor))
        vitals['respiratoryRate'] = max(10, min(25, baseline['respiratoryRate'] + random.randint(-4, 6) * variation_factor))
        vitals['glucose'] = max(70, min(180, baseline['glucose'] + random.randint(-30, 40) * variation_factor))
        
        return vitals
    
    def simulate_patient_vitals(self, monitor_id: str, patient_profile: PatientProfile):
        """Simulate vitals for a single patient with realistic risk patterns"""
        try:
            current_time = datetime.now()
            
            # Check if we should start a new risk scenario
            if not patient_profile.scenario:
                new_scenario = self.vital_pattern_generator.should_start_risk_scenario(patient_profile)
                if new_scenario:
                    patient_profile.scenario = new_scenario.value
                    patient_profile.scenario_start_time = current_time
                    patient_profile.scenario_progression = 0.0
                    logger.info(f"Starting risk scenario '{new_scenario.value}' for patient {patient_profile.patientId}")
            
            # Generate vitals based on current scenario or normal state
            if patient_profile.scenario and patient_profile.scenario_start_time:
                # Calculate progression (0.0 to 1.0) based on time elapsed
                time_elapsed = (current_time - patient_profile.scenario_start_time).total_seconds() / 60  # minutes
                patient_profile.scenario_progression = min(1.0, time_elapsed / 15.0)  # 15 minutes to full progression (reduced from 30)
                
                # Generate scenario-based vitals
                scenario_enum = RiskScenario(patient_profile.scenario)
                vitals = self.vital_pattern_generator.generate_scenario_vitals(
                    scenario_enum, 
                    patient_profile.baselineVitals, 
                    patient_profile.scenario_progression,
                    int(time_elapsed)
                )
                
                # Scenario ends after some time or recovers
                if patient_profile.scenario_progression >= 1.0 and random.random() < 0.2:  # 20% chance to end each cycle (increased from 10%)
                    patient_profile.scenario = None
                    patient_profile.scenario_start_time = None
                    patient_profile.scenario_progression = 0.0
                    logger.info(f"Risk scenario ended for patient {patient_profile.patientId}")
            else:
                # Generate normal vitals with natural variation (increased variation for critical patients)
                variation = 2.0 if patient_profile.currentState == 'critical' else 1.5
                vitals = self.generate_normal_vitals(patient_profile.baselineVitals, variation)
            
            # Add common fields
            vitals.update({
                'bloodPressure': {
                    'systolic': vitals.pop('systolicBP'),
                    'diastolic': vitals.pop('diastolicBP')
                },
                'bedOccupancy': True,
                'patientId': patient_profile.patientId,
                'deviceStatus': 'online',
                'batteryLevel': 85 + random.randint(0, 14),
                'signalStrength': 85 + random.randint(0, 14),
                'timestamp': format_datetime_for_firebase(current_time)
            })
            
            # Save to Firebase using the correct structure: vitals/{patient_id}/{timestamp}
            monitor_ref = db.reference(f'iotData/{monitor_id}/vitals/{patient_profile.patientId}')
            monitor_ref.child(format_datetime_for_firebase(current_time)).set(vitals)
            
            # Log concerning vital patterns for debugging
            if patient_profile.scenario:
                logger.info(f"🩺 Patient {patient_profile.patientId} in scenario '{patient_profile.scenario}' "
                           f"(progression: {patient_profile.scenario_progression:.2f}) - "
                           f"HR: {vitals['heartRate']}, BP: {vitals['bloodPressure']['systolic']}/{vitals['bloodPressure']['diastolic']}, "
                           f"O2: {vitals['oxygenLevel']:.1f}%, Temp: {vitals['temperature']:.1f}°C, Glucose: {vitals['glucose']:.0f}")
            else:
                # Also log normal vitals occasionally to show variation
                if random.random() < 0.3:  # 30% chance to log normal vitals
                    logger.info(f"📊 Patient {patient_profile.patientId} normal vitals - "
                               f"HR: {vitals['heartRate']}, BP: {vitals['bloodPressure']['systolic']}/{vitals['bloodPressure']['diastolic']}, "
                               f"O2: {vitals['oxygenLevel']:.1f}%, Temp: {vitals['temperature']:.1f}°C, Glucose: {vitals['glucose']:.0f}")
            
        except Exception as e:
            logger.error(f"Error simulating vitals for monitor {monitor_id}: {str(e)}")
    
    def simulate_environmental_data(self, sensor_id: str, sensor_info: Dict):
        """Simulate environmental data for a sensor"""
        try:
            current_time = datetime.now()
            room_type = sensor_info.get('roomType', 'general_ward')
            
            # Generate environmental data
            env_data = self.env_data_generator.generate_environmental_data(room_type)
            
            # Add device status fields
            env_data.update({
                'deviceStatus': 'online',
                'batteryLevel': 90 + random.randint(0, 9),
                'signalStrength': 85 + random.randint(0, 14),
                'timestamp': format_datetime_for_firebase(current_time)
            })
            
            # Save to Firebase
            sensor_ref = db.reference(f'iotData/{sensor_id}/environmentalData')
            sensor_ref.child(format_datetime_for_firebase(current_time)).set(env_data)
            
        except Exception as e:
            logger.error(f"Error simulating environmental data for sensor {sensor_id}: {str(e)}")
    
    def start_enhanced_simulation(self):
        """Start the enhanced simulation with anomaly generation"""
        global shutdown_requested
        logger.info("Starting enhanced hospital data simulation with anomaly generation...")
        
        # Load patient profiles
        self.load_patient_profiles()
        
        if not self.patient_profiles and not self.environmental_sensors:
            logger.error("No patient profiles or environmental sensors loaded. Cannot start simulation.")
            logger.error("This usually means:")
            logger.error("1. No IoT devices are configured in Firebase")
            logger.error("2. No patients are assigned to devices")
            logger.error("3. Firebase connection issues")
            return
        
        logger.info(f"Starting simulation with {len(self.patient_profiles)} patients and {len(self.environmental_sensors)} environmental sensors")
        
        while not shutdown_requested:
            try:
                self.simulation_cycle += 1
                logger.info(f"Simulation cycle {self.simulation_cycle}")
                
                # Simulate patient vitals
                vitals_simulated = 0
                for monitor_id, patient_profile in self.patient_profiles.items():
                    if shutdown_requested:
                        break
                    logger.debug(f"Simulating vitals for monitor {monitor_id}, patient {patient_profile.patientId}")
                    self.simulate_patient_vitals(monitor_id, patient_profile)
                    vitals_simulated += 1
                
                # Simulate environmental data
                env_simulated = 0
                for sensor_id, sensor_info in self.environmental_sensors.items():
                    if shutdown_requested:
                        break
                    logger.debug(f"Simulating environmental data for sensor {sensor_id}")
                    self.simulate_environmental_data(sensor_id, sensor_info)
                    env_simulated += 1
                
                logger.info(f"Cycle {self.simulation_cycle} complete: {vitals_simulated} vitals, {env_simulated} environmental readings")
                
                # Check for anomalies every few cycles (to avoid overwhelming the API)
                if self.simulation_cycle % 2 == 0:  # Check every other cycle (every ~10 seconds)
                    logger.info("Running anomaly detection checks...")
                    anomaly_results = self.anomaly_detector.check_all_patients(self.patient_profiles)
                    
                    # Log anomaly detection summary
                    anomalies_found = sum(1 for result in anomaly_results.values() if result is not None)
                    if anomalies_found > 0:
                        logger.warning(f"Anomaly detection found issues for {anomalies_found} patients")
                        summary = self.anomaly_detector.get_anomaly_summary()
                        logger.info(f"Anomaly Summary: {summary}")
                    else:
                        logger.info("No new anomalies detected")
                
                # Periodically reload patient profiles to catch updates
                if self.simulation_cycle % 20 == 0:  # Every 20 cycles (~100 seconds)
                    logger.info("Reloading patient profiles...")
                    self.load_patient_profiles()
                
                # Sleep with periodic checks for shutdown
                for _ in range(5):  # 5 seconds total, check every second
                    if shutdown_requested:
                        break
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in simulation cycle: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                if not shutdown_requested:
                    time.sleep(5)
        
        logger.info("Enhanced simulation stopped gracefully")

def main():
    """Main function to start the enhanced simulation"""
    try:
        logger.info("Initializing Enhanced Hospital Data Simulator...")
        simulator = EnhancedHospitalDataSimulator()
        simulator.start_enhanced_simulation()
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
    except Exception as e:
        logger.error(f"Error in enhanced simulation: {str(e)}")
    finally:
        logger.info("Enhanced simulation terminated")

if __name__ == "__main__":
    main()
