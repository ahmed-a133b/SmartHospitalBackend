import os
import json
import time
import random
import signal
import sys
import math
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

class AlertLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AnomalyType(Enum):
    CARDIAC_ARRHYTHMIA = "cardiac_arrhythmia"
    HYPERTENSIVE_CRISIS = "hypertensive_crisis"
    HYPOTENSIVE_SHOCK = "hypotensive_shock"
    RESPIRATORY_DISTRESS = "respiratory_distress"
    HYPOXEMIA = "hypoxemia"
    FEVER_SPIKE = "fever_spike"
    HYPOTHERMIA = "hypothermia"
    HYPERGLYCEMIA = "hyperglycemia"
    HYPOGLYCEMIA = "hypoglycemia"
    TACHYCARDIA = "tachycardia"
    BRADYCARDIA = "bradycardia"
    ENVIRONMENTAL_HAZARD = "environmental_hazard"
    PATIENT_FALL_RISK = "patient_fall_risk"
    MEDICATION_INTERACTION = "medication_interaction"

@dataclass
class Alert:
    message: str
    monitorId: str
    patientId: str
    resolved: bool
    timestamp: str
    type: str  # "warning", "critical", "info"
    vitals: Dict
    environmentalValues: Optional[Dict] = None
    recommendations: List[str] = None

@dataclass
class PatientProfile:
    patientId: str
    age: int
    conditions: List[str]
    medications: List[str]
    riskFactors: List[str]
    baselineVitals: Dict
    currentState: str  # stable, deteriorating, critical, recovering

class MedicalScenarioGenerator:
    """Generates realistic medical scenarios and anomalies"""
    
    def __init__(self):
        self.active_scenarios = {}  # deviceId -> scenario info
        self.scenario_probabilities = {
            AnomalyType.CARDIAC_ARRHYTHMIA: 0.02,
            AnomalyType.HYPERTENSIVE_CRISIS: 0.015,
            AnomalyType.HYPOTENSIVE_SHOCK: 0.01,
            AnomalyType.RESPIRATORY_DISTRESS: 0.025,
            AnomalyType.HYPOXEMIA: 0.02,
            AnomalyType.FEVER_SPIKE: 0.03,
            AnomalyType.HYPOTHERMIA: 0.008,
            AnomalyType.HYPERGLYCEMIA: 0.025,
            AnomalyType.HYPOGLYCEMIA: 0.015,
            AnomalyType.TACHYCARDIA: 0.03,
            AnomalyType.BRADYCARDIA: 0.02,
        }
    
    def should_trigger_anomaly(self, patient_profile: PatientProfile) -> Optional[AnomalyType]:
        """Determine if an anomaly should be triggered based on patient risk factors"""
        # Increase probabilities based on patient conditions
        adjusted_probabilities = self.scenario_probabilities.copy()
        
        if 'heart_disease' in patient_profile.conditions:
            adjusted_probabilities[AnomalyType.CARDIAC_ARRHYTHMIA] *= 3
            adjusted_probabilities[AnomalyType.TACHYCARDIA] *= 2
            adjusted_probabilities[AnomalyType.BRADYCARDIA] *= 2
        
        if 'hypertension' in patient_profile.conditions:
            adjusted_probabilities[AnomalyType.HYPERTENSIVE_CRISIS] *= 4
        
        if 'diabetes' in patient_profile.conditions:
            adjusted_probabilities[AnomalyType.HYPERGLYCEMIA] *= 5
            adjusted_probabilities[AnomalyType.HYPOGLYCEMIA] *= 3
        
        if 'copd' in patient_profile.conditions or 'asthma' in patient_profile.conditions:
            adjusted_probabilities[AnomalyType.RESPIRATORY_DISTRESS] *= 4
            adjusted_probabilities[AnomalyType.HYPOXEMIA] *= 3
        
        if patient_profile.age > 70:
            for anomaly_type in adjusted_probabilities:
                adjusted_probabilities[anomaly_type] *= 1.5
        
        if patient_profile.currentState == 'critical':
            for anomaly_type in adjusted_probabilities:
                adjusted_probabilities[anomaly_type] *= 2
        
        # Check for anomaly trigger
        for anomaly_type, probability in adjusted_probabilities.items():
            if random.random() < probability:
                return anomaly_type
        
        return None
    
    def generate_anomaly_vitals(self, anomaly_type: AnomalyType, baseline_vitals: Dict, severity: float = 1.0) -> Tuple[Dict, AlertLevel]:
        """Generate vital signs for a specific anomaly"""
        vitals = baseline_vitals.copy()
        alert_level = AlertLevel.LOW
        
        if anomaly_type == AnomalyType.CARDIAC_ARRHYTHMIA:
            # Irregular heart rate with high variability
            base_hr = baseline_vitals['heartRate']
            vitals['heartRate'] = base_hr + random.randint(-30, 50) * severity
            vitals['heartRate'] = max(40, min(200, vitals['heartRate']))
            alert_level = AlertLevel.HIGH if severity > 0.7 else AlertLevel.MEDIUM
            
        elif anomaly_type == AnomalyType.HYPERTENSIVE_CRISIS:
            vitals['systolicBP'] = baseline_vitals['systolicBP'] + random.randint(40, 80) * severity
            vitals['diastolicBP'] = baseline_vitals['diastolicBP'] + random.randint(20, 40) * severity
            vitals['heartRate'] = baseline_vitals['heartRate'] + random.randint(10, 30)
            alert_level = AlertLevel.CRITICAL if vitals['systolicBP'] > 180 else AlertLevel.HIGH
            
        elif anomaly_type == AnomalyType.HYPOTENSIVE_SHOCK:
            vitals['systolicBP'] = max(60, baseline_vitals['systolicBP'] - random.randint(30, 60) * severity)
            vitals['diastolicBP'] = max(40, baseline_vitals['diastolicBP'] - random.randint(15, 30) * severity)
            vitals['heartRate'] = baseline_vitals['heartRate'] + random.randint(20, 40)
            vitals['temperature'] = baseline_vitals['temperature'] - random.uniform(0.5, 1.5)
            alert_level = AlertLevel.CRITICAL
            
        elif anomaly_type == AnomalyType.RESPIRATORY_DISTRESS:
            vitals['respiratoryRate'] = baseline_vitals['respiratoryRate'] + random.randint(8, 20) * severity
            vitals['oxygenLevel'] = max(75, baseline_vitals['oxygenLevel'] - random.randint(5, 15) * severity)
            vitals['heartRate'] = baseline_vitals['heartRate'] + random.randint(10, 25)
            alert_level = AlertLevel.HIGH if vitals['oxygenLevel'] < 88 else AlertLevel.MEDIUM
            
        elif anomaly_type == AnomalyType.HYPOXEMIA:
            vitals['oxygenLevel'] = max(70, baseline_vitals['oxygenLevel'] - random.randint(8, 20) * severity)
            vitals['respiratoryRate'] = baseline_vitals['respiratoryRate'] + random.randint(5, 15)
            vitals['heartRate'] = baseline_vitals['heartRate'] + random.randint(10, 20)
            alert_level = AlertLevel.CRITICAL if vitals['oxygenLevel'] < 80 else AlertLevel.HIGH
            
        elif anomaly_type == AnomalyType.FEVER_SPIKE:
            vitals['temperature'] = baseline_vitals['temperature'] + random.uniform(1.0, 3.5) * severity
            vitals['heartRate'] = baseline_vitals['heartRate'] + random.randint(15, 30)
            vitals['respiratoryRate'] = baseline_vitals['respiratoryRate'] + random.randint(3, 8)
            alert_level = AlertLevel.HIGH if vitals['temperature'] > 39.5 else AlertLevel.MEDIUM
            
        elif anomaly_type == AnomalyType.HYPOTHERMIA:
            vitals['temperature'] = max(32.0, baseline_vitals['temperature'] - random.uniform(2.0, 5.0) * severity)
            vitals['heartRate'] = max(40, baseline_vitals['heartRate'] - random.randint(10, 30))
            vitals['respiratoryRate'] = max(8, baseline_vitals['respiratoryRate'] - random.randint(2, 6))
            alert_level = AlertLevel.CRITICAL if vitals['temperature'] < 35.0 else AlertLevel.HIGH
            
        elif anomaly_type == AnomalyType.HYPERGLYCEMIA:
            vitals['glucose'] = baseline_vitals['glucose'] + random.randint(100, 300) * severity
            vitals['heartRate'] = baseline_vitals['heartRate'] + random.randint(5, 15)
            vitals['respiratoryRate'] = baseline_vitals['respiratoryRate'] + random.randint(2, 6)
            alert_level = AlertLevel.CRITICAL if vitals['glucose'] > 400 else AlertLevel.HIGH
            
        elif anomaly_type == AnomalyType.HYPOGLYCEMIA:
            vitals['glucose'] = max(30, baseline_vitals['glucose'] - random.randint(40, 70) * severity)
            vitals['heartRate'] = baseline_vitals['heartRate'] + random.randint(10, 25)
            vitals['temperature'] = baseline_vitals['temperature'] - random.uniform(0.2, 0.8)
            alert_level = AlertLevel.CRITICAL if vitals['glucose'] < 50 else AlertLevel.HIGH
            
        elif anomaly_type == AnomalyType.TACHYCARDIA:
            vitals['heartRate'] = baseline_vitals['heartRate'] + random.randint(30, 70) * severity
            vitals['heartRate'] = min(220, vitals['heartRate'])
            alert_level = AlertLevel.HIGH if vitals['heartRate'] > 150 else AlertLevel.MEDIUM
            
        elif anomaly_type == AnomalyType.BRADYCARDIA:
            vitals['heartRate'] = max(30, baseline_vitals['heartRate'] - random.randint(20, 40) * severity)
            alert_level = AlertLevel.HIGH if vitals['heartRate'] < 50 else AlertLevel.MEDIUM
        
        return vitals, alert_level

class EnvironmentalHazardGenerator:
    """Generates environmental hazards and anomalies"""
    
    def __init__(self):
        self.hazard_probabilities = {
            'temperature_extreme': 0.01,
            'humidity_extreme': 0.015,
            'air_quality_poor': 0.02,
            'noise_excessive': 0.008,
            'lighting_failure': 0.005,
            'contamination_risk': 0.003
        }
    
    def should_trigger_environmental_hazard(self, room_type: str) -> Optional[str]:
        """Determine if an environmental hazard should be triggered"""
        adjusted_probabilities = self.hazard_probabilities.copy()
        
        # Adjust probabilities based on room type
        if room_type in ['icu', 'emergency']:
            for hazard in adjusted_probabilities:
                adjusted_probabilities[hazard] *= 0.5  # ICU/ER have better monitoring
        elif room_type in ['general_ward']:
            for hazard in adjusted_probabilities:
                adjusted_probabilities[hazard] *= 1.2
        
        for hazard, probability in adjusted_probabilities.items():
            if random.random() < probability:
                return hazard
        
        return None
    
    def generate_hazard_environmental_data(self, hazard_type: str, baseline_env: Dict) -> Tuple[Dict, AlertLevel]:
        """Generate environmental data for a specific hazard"""
        env_data = baseline_env.copy()
        alert_level = AlertLevel.LOW
        
        if hazard_type == 'temperature_extreme':
            if random.choice([True, False]):  # Hot or cold extreme
                env_data['temperature'] = baseline_env['temperature'] + random.uniform(5, 12)
                alert_level = AlertLevel.HIGH if env_data['temperature'] > 28 else AlertLevel.MEDIUM
            else:
                env_data['temperature'] = baseline_env['temperature'] - random.uniform(3, 8)
                alert_level = AlertLevel.HIGH if env_data['temperature'] < 18 else AlertLevel.MEDIUM
                
        elif hazard_type == 'humidity_extreme':
            if random.choice([True, False]):  # High or low humidity
                env_data['humidity'] = min(95, baseline_env['humidity'] + random.uniform(15, 30))
                alert_level = AlertLevel.MEDIUM if env_data['humidity'] > 70 else AlertLevel.LOW
            else:
                env_data['humidity'] = max(10, baseline_env['humidity'] - random.uniform(10, 25))
                alert_level = AlertLevel.MEDIUM if env_data['humidity'] < 30 else AlertLevel.LOW
                
        elif hazard_type == 'air_quality_poor':
            env_data['airQuality'] = max(0, baseline_env['airQuality'] - random.uniform(20, 40))
            env_data['co2Level'] = baseline_env['co2Level'] + random.uniform(200, 800)
            alert_level = AlertLevel.HIGH if env_data['airQuality'] < 30 else AlertLevel.MEDIUM
            
        elif hazard_type == 'noise_excessive':
            env_data['noiseLevel'] = baseline_env['noiseLevel'] + random.uniform(15, 35)
            alert_level = AlertLevel.MEDIUM if env_data['noiseLevel'] > 70 else AlertLevel.LOW
            
        elif hazard_type == 'contamination_risk':
            env_data['airQuality'] = max(10, baseline_env['airQuality'] - random.uniform(30, 50))
            env_data['particleCount'] = baseline_env.get('particleCount', 100) + random.uniform(500, 2000)
            alert_level = AlertLevel.HIGH
        
        return env_data, alert_level

def format_datetime_for_firebase(dt):
    """Format datetime in a Firebase-safe format"""
    return dt.strftime("%Y-%m-%d_%H-%M-%S")

class EnhancedHospitalDataSimulator:
    def __init__(self):
        self.init_firebase()
        self.scenario_generator = MedicalScenarioGenerator()
        self.hazard_generator = EnvironmentalHazardGenerator()
        self.patient_profiles = {}
        self.environmental_sensors = {}
        self.active_alerts = {}
        self.simulation_cycle = 0
        
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
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred, {
                    'databaseURL': db_url
                })
        except json.JSONDecodeError as e:
            raise ValueError("Invalid FIREBASE_KEY_JSON") from e
    
    def load_patient_profiles(self):
        """Load patient data and create profiles for simulation"""
        try:
            # Get monitors and their assigned patients
            iot_ref = db.reference('iotData')
            monitors_data = iot_ref.get()
            
            if not monitors_data:
                logger.warning("No IoT monitors found")
                return
            
            # Get patient data
            patients_ref = db.reference('patients')
            patients_data = patients_ref.get() or {}
            
            for monitor_id, monitor_data in monitors_data.items():
                device_info = monitor_data.get('deviceInfo', {})
                
                if device_info.get('type') == 'vitals_monitor':
                    # Get patient ID from latest vitals or device info
                    patient_id = device_info.get('currentPatientId')
                    
                    if not patient_id:
                        # Try to get from latest vitals - check if we have vitals organized by patient
                        vitals = monitor_data.get('vitals', {})
                        if vitals:
                            # With new structure, vitals are organized as vitals[patient_id][timestamp]
                            # Get the most recent patient that has vitals
                            for potential_patient_id, patient_vitals in vitals.items():
                                if patient_vitals:  # This patient has vitals data
                                    patient_id = potential_patient_id
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
                        logger.info(f"Loaded profile for patient {patient_id} on monitor {monitor_id}")
                
                elif device_info.get('type') == 'environmental_sensor':
                    # Store environmental sensor info
                    self.environmental_sensors[monitor_id] = {
                        'roomId': device_info.get('roomId'),
                        'roomType': device_info.get('roomType', 'general_ward'),
                        'deviceInfo': device_info
                    }
            
            logger.info(f"Loaded {len(self.patient_profiles)} patient profiles and {len(self.environmental_sensors)} environmental sensors")
            
        except Exception as e:
            logger.error(f"Error loading patient profiles: {str(e)}")
    
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
        
        # Add realistic variation to each vital sign
        vitals['heartRate'] = max(50, min(100, baseline['heartRate'] + random.randint(-5, 5) * variation_factor))
        vitals['oxygenLevel'] = max(95, min(100, baseline['oxygenLevel'] + random.uniform(-1, 1) * variation_factor))
        vitals['temperature'] = max(36.0, min(38.0, baseline['temperature'] + random.uniform(-0.3, 0.3) * variation_factor))
        vitals['systolicBP'] = max(90, min(140, baseline['systolicBP'] + random.randint(-10, 10) * variation_factor))
        vitals['diastolicBP'] = max(60, min(90, baseline['diastolicBP'] + random.randint(-5, 5) * variation_factor))
        vitals['respiratoryRate'] = max(12, min(20, baseline['respiratoryRate'] + random.randint(-2, 2) * variation_factor))
        vitals['glucose'] = max(80, min(140, baseline['glucose'] + random.randint(-15, 15) * variation_factor))
        
        return vitals
    
    def generate_environmental_data(self, room_type: str, baseline: Optional[Dict] = None) -> Dict:
        """Generate environmental sensor data"""
        if baseline is None:
            baseline = {
                'temperature': 22.0,
                'humidity': 45.0,
                'airQuality': 85.0,
                'noiseLevel': 35.0,
                'co2Level': 400.0,
                'lightLevel': 300.0
            }
        
        # Add natural variation
        env_data = {
            'temperature': baseline['temperature'] + random.uniform(-1, 1),
            'humidity': max(30, min(70, baseline['humidity'] + random.uniform(-5, 5))),
            'airQuality': max(50, min(100, baseline['airQuality'] + random.uniform(-5, 5))),
            'noiseLevel': max(25, baseline['noiseLevel'] + random.uniform(-5, 10)),
            'co2Level': max(350, baseline['co2Level'] + random.uniform(-50, 100)),
            'lightLevel': max(200, baseline['lightLevel'] + random.uniform(-50, 50))
        }
        
        return env_data
    
    def create_alert(self, device_id: str, patient_id: str, anomaly_type: AnomalyType, 
                    alert_level: AlertLevel, vitals: Dict, env_data: Optional[Dict] = None) -> Tuple[Alert, str]:
        """Create an alert for an anomaly"""
        current_time = datetime.now()
        timestamp = format_datetime_for_firebase(current_time)
        
        # Generate appropriate message and recommendations
        message, recommendations = self.get_alert_message_and_recommendations(anomaly_type, vitals, env_data)
        
        # Convert alert level to type format matching your schema
        alert_type_map = {
            AlertLevel.LOW: "info",
            AlertLevel.MEDIUM: "warning", 
            AlertLevel.HIGH: "warning",
            AlertLevel.CRITICAL: "critical"
        }
        
        # Clean vitals data to match your format (remove extra fields)
        clean_vitals = {
            'heartRate': vitals.get('heartRate'),
            'oxygenLevel': vitals.get('oxygenLevel'),
            'temperature': vitals.get('temperature'),
            'respiratoryRate': vitals.get('respiratoryRate'),
            'bloodPressure': vitals.get('bloodPressure', {})
        }
        
        # Remove None values
        clean_vitals = {k: v for k, v in clean_vitals.items() if v is not None}
        
        alert = Alert(
            message=message,
            monitorId=device_id,
            patientId=patient_id,
            resolved=False,
            timestamp=timestamp,
            type=alert_type_map.get(alert_level, "warning"),
            vitals=clean_vitals,
            environmentalValues=env_data,
            recommendations=recommendations
        )
        
        return alert, timestamp
    
    def get_alert_message_and_recommendations(self, anomaly_type: AnomalyType, vitals: Dict, env_data: Optional[Dict]) -> Tuple[str, List[str]]:
        """Generate alert message and recommendations based on anomaly type"""
        messages = {
            AnomalyType.CARDIAC_ARRHYTHMIA: f"Cardiac arrhythmia detected - HR: {vitals.get('heartRate', 'N/A')} bpm",
            AnomalyType.HYPERTENSIVE_CRISIS: f"Hypertensive crisis - BP: {vitals.get('systolicBP', 'N/A')}/{vitals.get('diastolicBP', 'N/A')} mmHg",
            AnomalyType.HYPOTENSIVE_SHOCK: f"Hypotensive shock - BP: {vitals.get('systolicBP', 'N/A')}/{vitals.get('diastolicBP', 'N/A')} mmHg",
            AnomalyType.RESPIRATORY_DISTRESS: f"Respiratory distress - RR: {vitals.get('respiratoryRate', 'N/A')}, SpO2: {vitals.get('oxygenLevel', 'N/A')}%",
            AnomalyType.HYPOXEMIA: f"Severe hypoxemia - SpO2: {vitals.get('oxygenLevel', 'N/A')}%",
            AnomalyType.FEVER_SPIKE: f"High fever detected - Temp: {vitals.get('temperature', 'N/A')}°C",
            AnomalyType.HYPOTHERMIA: f"Hypothermia detected - Temp: {vitals.get('temperature', 'N/A')}°C",
            AnomalyType.HYPERGLYCEMIA: f"Severe hyperglycemia - Glucose: {vitals.get('glucose', 'N/A')} mg/dL",
            AnomalyType.HYPOGLYCEMIA: f"Severe hypoglycemia - Glucose: {vitals.get('glucose', 'N/A')} mg/dL",
            AnomalyType.TACHYCARDIA: f"Tachycardia detected - HR: {vitals.get('heartRate', 'N/A')} bpm",
            AnomalyType.BRADYCARDIA: f"Bradycardia detected - HR: {vitals.get('heartRate', 'N/A')} bpm",
        }
        
        recommendations_map = {
            AnomalyType.CARDIAC_ARRHYTHMIA: ["Obtain 12-lead ECG", "Check electrolytes", "Consider cardiology consult", "Monitor continuously"],
            AnomalyType.HYPERTENSIVE_CRISIS: ["Administer antihypertensive medication", "Neurological assessment", "Consider ICU transfer", "Check for end-organ damage"],
            AnomalyType.HYPOTENSIVE_SHOCK: ["IV fluid resuscitation", "Vasopressor support", "Identify underlying cause", "Consider ICU transfer"],
            AnomalyType.RESPIRATORY_DISTRESS: ["Administer oxygen", "Arterial blood gas analysis", "Chest X-ray", "Consider mechanical ventilation"],
            AnomalyType.HYPOXEMIA: ["High-flow oxygen therapy", "Arterial blood gas", "Consider intubation", "Identify underlying cause"],
            AnomalyType.FEVER_SPIKE: ["Antipyretic medication", "Blood cultures", "Infection workup", "Cooling measures"],
            AnomalyType.HYPOTHERMIA: ["Active warming measures", "Avoid rapid rewarming", "Monitor cardiac rhythm", "Check for underlying causes"],
            AnomalyType.HYPERGLYCEMIA: ["Insulin therapy", "Check ketones", "IV fluids", "Monitor electrolytes"],
            AnomalyType.HYPOGLYCEMIA: ["Immediate glucose administration", "Monitor closely", "Identify cause", "Adjust medications"],
            AnomalyType.TACHYCARDIA: ["12-lead ECG", "Check hemodynamic stability", "Identify underlying cause", "Consider rate control"],
            AnomalyType.BRADYCARDIA: ["Check hemodynamic stability", "Consider atropine", "External pacing if severe", "Identify reversible causes"],
        }
        
        message = messages.get(anomaly_type, f"Anomaly detected: {anomaly_type.value}")
        recommendations = recommendations_map.get(anomaly_type, ["Assess patient immediately", "Notify physician"])
        
        return message, recommendations
    
    def save_alert_to_firebase(self, alert: Alert, timestamp: str):
        """Save alert to Firebase using timestamp as key"""
        try:
            alerts_ref = db.reference('alerts')
            # Convert the alert to dict - no need to handle enums anymore
            alert_dict = asdict(alert)
            # Remove None values to keep the JSON clean
            alert_dict = {k: v for k, v in alert_dict.items() if v is not None}
            # Store using timestamp as key
            alerts_ref.child(timestamp).set(alert_dict)
            logger.info(f"Alert saved with timestamp {timestamp}: {alert.type} - {alert.message}")
        except Exception as e:
            logger.error(f"Error saving alert: {str(e)}")
    
    def simulate_patient_vitals(self, monitor_id: str, patient_profile: PatientProfile):
        """Simulate vitals for a single patient"""
        try:
            current_time = datetime.now()
            
            # Check for anomaly trigger
            anomaly_type = self.scenario_generator.should_trigger_anomaly(patient_profile)
            
            if anomaly_type:
                # Generate anomaly vitals
                severity = random.uniform(0.5, 1.0)
                vitals, alert_level = self.scenario_generator.generate_anomaly_vitals(
                    anomaly_type, patient_profile.baselineVitals, severity
                )
                
                # Create and save alert
                alert, alert_timestamp = self.create_alert(monitor_id, patient_profile.patientId, anomaly_type, alert_level, vitals)
                self.save_alert_to_firebase(alert, alert_timestamp)
                
                logger.warning(f"ANOMALY: {anomaly_type.value} for patient {patient_profile.patientId} - Alert Level: {alert_level.value}")
            else:
                # Generate normal vitals with natural variation
                variation = 1.2 if patient_profile.currentState == 'critical' else 1.0
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
            
        except Exception as e:
            logger.error(f"Error simulating vitals for monitor {monitor_id}: {str(e)}")
    
    def simulate_environmental_data(self, sensor_id: str, sensor_info: Dict):
        """Simulate environmental data for a sensor"""
        try:
            current_time = datetime.now()
            room_type = sensor_info.get('roomType', 'general_ward')
            
            # Generate base environmental data
            env_data = self.generate_environmental_data(room_type)
            
            # Check for environmental hazard
            hazard_type = self.hazard_generator.should_trigger_environmental_hazard(room_type)
            
            if hazard_type:
                # Generate hazard data
                env_data, alert_level = self.hazard_generator.generate_hazard_environmental_data(hazard_type, env_data)
                
                # Create environmental alert
                current_time = datetime.now()
                env_timestamp = format_datetime_for_firebase(current_time)
                
                # Convert alert level to type format
                alert_type_map = {
                    AlertLevel.LOW: "info",
                    AlertLevel.MEDIUM: "warning", 
                    AlertLevel.HIGH: "warning",
                    AlertLevel.CRITICAL: "critical"
                }
                
                alert = Alert(
                    message=f"Environmental hazard: {hazard_type} in room {sensor_info.get('roomId', 'unknown')}",
                    monitorId=sensor_id,
                    patientId="N/A",
                    resolved=False,
                    timestamp=env_timestamp,
                    type=alert_type_map.get(alert_level, "warning"),
                    vitals={},  # No vitals for environmental alerts
                    environmentalValues=env_data,
                    recommendations=[
                        "Check room environmental controls",
                        "Assess patient comfort and safety",
                        "Notify facilities management",
                        "Consider patient relocation if severe"
                    ]
                )
                
                self.save_alert_to_firebase(alert, env_timestamp)
                logger.warning(f"ENVIRONMENTAL HAZARD: {hazard_type} in room {sensor_info.get('roomId')}")
            
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
            return
        
        while not shutdown_requested:
            try:
                self.simulation_cycle += 1
                logger.info(f"Simulation cycle {self.simulation_cycle}")
                
                # Simulate patient vitals
                for monitor_id, patient_profile in self.patient_profiles.items():
                    if shutdown_requested:
                        break
                    self.simulate_patient_vitals(monitor_id, patient_profile)
                
                # Simulate environmental data
                for sensor_id, sensor_info in self.environmental_sensors.items():
                    if shutdown_requested:
                        break
                    self.simulate_environmental_data(sensor_id, sensor_info)
                
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
