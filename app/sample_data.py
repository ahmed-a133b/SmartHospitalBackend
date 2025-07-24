from datetime import datetime, timedelta
import random

def format_datetime_for_firebase(dt):
    """Format datetime in a Firebase-safe format (no colons or special chars)"""
    return dt.strftime("%Y-%m-%d_%H-%M-%S")

def generate_sample_data():
    """Generate comprehensive sample data for the entire hospital database"""
    current_time = datetime.now()
    
    # Generate rooms first as they'll be referenced by other entities
    rooms_data = {
        "room_1": {
            "details": {
                "ward": "Cardiology",
                "type": "ICU",
                "capacity": 2,
                "equipment": [
                    {
                        "name": "Defibrillator",
                        "type": "emergency",
                        "status": "operational",
                        "lastMaintenance": format_datetime_for_firebase(current_time - timedelta(days=15))
                    },
                    {
                        "name": "ECG Monitor",
                        "type": "monitoring",
                        "status": "operational",
                        "lastMaintenance": format_datetime_for_firebase(current_time - timedelta(days=30))
                    }
                ],
                "floor": 1,
                "coordinates": {"x": 10, "y": 20, "z": 0}
            },
            "currentStatus": {
                "occupied": True,
                "patientId": "patient_1",
                "staffAssigned": ["staff_1", "staff_4"],
                "lastUpdated": format_datetime_for_firebase(current_time),
                "cleaningStatus": "clean",
                "isolationRequired": False
            },
            "environmental": {
                "temperature": 22.5,
                "humidity": 45,
                "airQuality": 95,
                "lastMeasured": format_datetime_for_firebase(current_time)
            }
        },
        "room_2": {
            "details": {
                "ward": "Pulmonology",
                "type": "isolation",
                "capacity": 1,
                "equipment": [
                    {
                        "name": "Ventilator",
                        "type": "respiratory",
                        "status": "operational",
                        "lastMaintenance": format_datetime_for_firebase(current_time - timedelta(days=10))
                    }
                ],
                "floor": 2,
                "coordinates": {"x": 15, "y": 25, "z": 0}
            },
            "currentStatus": {
                "occupied": True,
                "patientId": "patient_2",
                "staffAssigned": ["staff_2"],
                "lastUpdated": format_datetime_for_firebase(current_time),
                "cleaningStatus": "clean",
                "isolationRequired": True
            },
            "environmental": {
                "temperature": 23.0,
                "humidity": 50,
                "airQuality": 98,
                "lightLevel": 75,
                "noiseLevel": 30,
                "lastMeasured": format_datetime_for_firebase(current_time)
            }
        },
        "room_3": {
            "details": {
                "ward": "Cardiology",
                "type": "general",
                "capacity": 2,
                "equipment": [
                    {
                        "name": "ECG Monitor",
                        "type": "monitoring",
                        "status": "maintenance",
                        "lastMaintenance": format_datetime_for_firebase(current_time - timedelta(days=45))
                    }
                ],
                "floor": 1,
                "coordinates": {"x": 20, "y": 20, "z": 0}
            },
            "currentStatus": {
                "occupied": True,
                "patientId": "patient_3",
                "staffAssigned": ["staff_3"],
                "lastUpdated": format_datetime_for_firebase(current_time),
                "cleaningStatus": "needs_cleaning",
                "isolationRequired": False
            },
            "environmental": {
                "temperature": 22.0,
                "humidity": 48,
                "airQuality": 92,
                "lightLevel": 85,
                "noiseLevel": 40,
                "lastMeasured": format_datetime_for_firebase(current_time)
            }
        }
    }

    # Generate beds data
    beds_data = {
        "bed_1": {
            "roomId": "room_1",
            "bedNumber": "1",
            "type": "ICU",
            "status": "occupied",
            "patientId": "patient_1",
            "features": ["adjustable", "monitoring", "ventilator_compatible"],
            "lastCleaned": format_datetime_for_firebase(current_time - timedelta(hours=12)),
            "position": {"x": 1, "y": 1, "rotation": 0}
        },
        "bed_2": {
            "roomId": "room_1",
            "bedNumber": "2",
            "type": "ICU",
            "status": "available",
            "features": ["adjustable", "monitoring", "ventilator_compatible"],
            "lastCleaned": format_datetime_for_firebase(current_time - timedelta(hours=2)),
            "position": {"x": 3, "y": 1, "rotation": 0}
        },
        "bed_3": {
            "roomId": "room_2",
            "bedNumber": "3",
            "type": "isolation",
            "status": "occupied",
            "patientId": "patient_2",
            "features": ["adjustable", "monitoring", "isolation_compatible"],
            "lastCleaned": format_datetime_for_firebase(current_time - timedelta(hours=24)),
            "position": {"x": 1, "y": 1, "rotation": 90}
        },
        "bed_4": {
            "roomId": "room_3",
            "bedNumber": "4",
            "type": "standard",
            "status": "occupied",
            "patientId": "patient_3",
            "features": ["adjustable", "monitoring"],
            "lastCleaned": format_datetime_for_firebase(current_time - timedelta(hours=36)),
            "position": {"x": 1, "y": 1, "rotation": 0}
        }
    }

    # Generate patients data
    patients_data = {
        "patient_1": {
            "personalInfo": {
                "name": "Robert Johnson",
                "age": 65,
                "gender": "Male",
                "admissionDate": format_datetime_for_firebase(current_time - timedelta(days=3)),
                "ward": "Cardiology",
                "roomId": "room_1",
                "bedId": "bed_1"
            },
            "medicalHistory": {
                "conditions": ["hypertension", "diabetes", "coronary_artery_disease"],
                "medications": [
                    {
                        "name": "Lisinopril",
                        "dosage": "10mg",
                        "frequency": "once daily",
                        "startDate": format_datetime_for_firebase(current_time - timedelta(days=30))
                    },
                    {
                        "name": "Metformin",
                        "dosage": "500mg",
                        "frequency": "twice daily",
                        "startDate": format_datetime_for_firebase(current_time - timedelta(days=90))
                    },
                    {
                        "name": "Aspirin",
                        "dosage": "81mg",
                        "frequency": "once daily",
                        "startDate": format_datetime_for_firebase(current_time - timedelta(days=180))
                    }
                ],
                "allergies": ["penicillin", "shellfish"],
                "lastCheckup": format_datetime_for_firebase(current_time - timedelta(hours=6)),
                "admissionReason": "Chest pain and elevated blood pressure"
            },
            "currentStatus": {
                "diagnosis": "Acute coronary syndrome",
                "status": "stable",
                "consciousness": "alert",
                "mobility": "limited",
                "lastUpdated": format_datetime_for_firebase(current_time - timedelta(minutes=30))
            },
            "predictions": {
                "riskLevel": "high",
                "riskScore": 75,
                "confidence": 0.85,
                "predictedAt": format_datetime_for_firebase(current_time - timedelta(minutes=15)),
                "nextPrediction": format_datetime_for_firebase(current_time + timedelta(hours=4)),
                "factors": ["elevated_blood_pressure", "cardiac_history", "age_factor"]
            }
        },
        "patient_2": {
            "personalInfo": {
                "name": "Maria Rodriguez",
                "age": 42,
                "gender": "Female",
                "admissionDate": format_datetime_for_firebase(current_time - timedelta(days=1)),
                "ward": "Pulmonology",
                "roomId": "room_2",
                "bedId": "bed_3"
            },
            "medicalHistory": {
                "conditions": ["asthma", "pneumonia"],
                "medications": [
                    {
                        "name": "Albuterol",
                        "dosage": "90mcg",
                        "frequency": "as needed",
                        "startDate": format_datetime_for_firebase(current_time - timedelta(days=1))
                    },
                    {
                        "name": "Prednisone",
                        "dosage": "20mg",
                        "frequency": "once daily",
                        "startDate": format_datetime_for_firebase(current_time - timedelta(days=1))
                    },
                    {
                        "name": "Azithromycin",
                        "dosage": "250mg",
                        "frequency": "once daily",
                        "startDate": format_datetime_for_firebase(current_time - timedelta(days=1))
                    }
                ],
                "allergies": ["latex"],
                "lastCheckup": format_datetime_for_firebase(current_time - timedelta(hours=2)),
                "admissionReason": "Severe asthma exacerbation with pneumonia"
            },
            "currentStatus": {
                "diagnosis": "Acute pneumonia with asthma exacerbation",
                "status": "critical",
                "consciousness": "alert",
                "mobility": "bedrest",
                "lastUpdated": format_datetime_for_firebase(current_time - timedelta(minutes=15))
            },
            "predictions": {
                "riskLevel": "critical",
                "riskScore": 90,
                "confidence": 0.92,
                "predictedAt": format_datetime_for_firebase(current_time - timedelta(minutes=10)),
                "nextPrediction": format_datetime_for_firebase(current_time + timedelta(hours=2)),
                "factors": ["respiratory_distress", "infection_markers", "oxygen_saturation"]
            }
        },
        "patient_3": {
            "personalInfo": {
                "name": "James Thompson",
                "age": 28,
                "gender": "Male",
                "admissionDate": format_datetime_for_firebase(current_time - timedelta(hours=8)),
                "ward": "Cardiology",
                "roomId": "room_3",
                "bedId": "bed_4"
            },
            "medicalHistory": {
                "conditions": ["anxiety", "palpitations"],
                "medications": [
                    {
                        "name": "Propranolol",
                        "dosage": "10mg",
                        "frequency": "as needed",
                        "startDate": format_datetime_for_firebase(current_time - timedelta(hours=6))
                    }
                ],
                "allergies": [],
                "lastCheckup": format_datetime_for_firebase(current_time - timedelta(hours=1)),
                "admissionReason": "Chest pain and palpitations, rule out cardiac causes"
            },
            "currentStatus": {
                "diagnosis": "Anxiety-related chest pain",
                "status": "stable",
                "consciousness": "alert",
                "mobility": "ambulatory",
                "lastUpdated": format_datetime_for_firebase(current_time - timedelta(minutes=45))
            },
            "predictions": {
                "riskLevel": "low",
                "riskScore": 25,
                "confidence": 0.78,
                "predictedAt": format_datetime_for_firebase(current_time - timedelta(minutes=30)),
                "nextPrediction": format_datetime_for_firebase(current_time + timedelta(hours=6)),
                "factors": ["vital_signs_stable", "young_age", "no_cardiac_history"]
            }
        }
    }

    # Generate IoT devices data with alerts
    iot_data = {
        "monitor_1": {
            "vitals": {
                format_datetime_for_firebase(current_time): {
                    "heartRate": 85,
                    "oxygenLevel": 96,
                    "temperature": 37.2,
                    "bloodPressure": {
                        "systolic": 145,
                        "diastolic": 95
                    },
                    "respiratoryRate": 18,
                    "glucose": 140,
                    "bedOccupancy": True,
                    "patientId": "patient_1",
                    "deviceStatus": "online",
                    "batteryLevel": 85,
                    "signalStrength": 95,
                    "timestamp": format_datetime_for_firebase(current_time)
                },
                format_datetime_for_firebase(current_time - timedelta(minutes=5)): {
                    "heartRate": 88,
                    "oxygenLevel": 95,
                    "temperature": 37.3,
                    "bloodPressure": {
                        "systolic": 150,
                        "diastolic": 98
                    },
                    "respiratoryRate": 20,
                    "glucose": 145,
                    "bedOccupancy": True,
                    "patientId": "patient_1",
                    "deviceStatus": "online",
                    "batteryLevel": 85,
                    "signalStrength": 94,
                    "timestamp": format_datetime_for_firebase(current_time - timedelta(minutes=5))
                }
            },
            "deviceInfo": {
                "type": "vitals_monitor",
                "manufacturer": "MedTech Systems",
                "model": "VM-2024",
                "roomId": "room_1",
                "bedId": "bed_1",
                "lastCalibrated": format_datetime_for_firebase(current_time - timedelta(days=7)),
                "calibrationDue": format_datetime_for_firebase(current_time + timedelta(days=23)),
                "maintenanceSchedule": format_datetime_for_firebase(current_time + timedelta(days=90))
            },
            "alerts": {
                "alert_1": {
                    "type": "critical",
                    "message": "Blood pressure critically high - 150/98 mmHg",
                    "timestamp": format_datetime_for_firebase(current_time - timedelta(minutes=5)),
                    "resolved": False,
                    "assignedTo": "staff_1"
                },
                "alert_2": {
                    "type": "warning",
                    "message": "Heart rate elevated - 88 bpm",
                    "timestamp": format_datetime_for_firebase(current_time - timedelta(minutes=10)),
                    "resolved": True,
                    "resolvedBy": "staff_4",
                    "resolvedAt": format_datetime_for_firebase(current_time - timedelta(minutes=2))
                }
            }
        },
        "monitor_2": {
            "vitals": {
                format_datetime_for_firebase(current_time): {
                    "heartRate": 110,
                    "oxygenLevel": 88,
                    "temperature": 38.5,
                    "bloodPressure": {
                        "systolic": 120,
                        "diastolic": 80
                    },
                    "respiratoryRate": 28,
                    "glucose": 95,
                    "bedOccupancy": True,
                    "patientId": "patient_2",
                    "deviceStatus": "online",
                    "batteryLevel": 92,
                    "signalStrength": 88,
                    "timestamp": format_datetime_for_firebase(current_time)
                }
            },
            "deviceInfo": {
                "type": "vitals_monitor",
                "manufacturer": "HealthMonitor Inc",
                "model": "HM-Pro",
                "roomId": "room_2",
                "bedId": "bed_3",
                "lastCalibrated": format_datetime_for_firebase(current_time - timedelta(days=3)),
                "calibrationDue": format_datetime_for_firebase(current_time + timedelta(days=27)),
                "maintenanceSchedule": format_datetime_for_firebase(current_time + timedelta(days=85))
            },
            "alerts": {
                "alert_3": {
                    "type": "critical",
                    "message": "Oxygen saturation critically low - 88%",
                    "timestamp": format_datetime_for_firebase(current_time - timedelta(minutes=2)),
                    "resolved": False,
                    "assignedTo": "staff_2"
                },
                "alert_4": {
                    "type": "critical",
                    "message": "High fever detected - 38.5°C",
                    "timestamp": format_datetime_for_firebase(current_time - timedelta(minutes=8)),
                    "resolved": False
                },
                "alert_5": {
                    "type": "warning",
                    "message": "Elevated respiratory rate - 28 breaths/min",
                    "timestamp": format_datetime_for_firebase(current_time - timedelta(minutes=15)),
                    "resolved": True,
                    "resolvedBy": "staff_2",
                    "resolvedAt": format_datetime_for_firebase(current_time - timedelta(minutes=12))
                }
            }
        },
        "monitor_3": {
            "vitals": {
                format_datetime_for_firebase(current_time): {
                    "heartRate": 72,
                    "oxygenLevel": 99,
                    "temperature": 36.8,
                    "bloodPressure": {
                        "systolic": 115,
                        "diastolic": 75
                    },
                    "respiratoryRate": 16,
                    "glucose": 90,
                    "bedOccupancy": True,
                    "patientId": "patient_3",
                    "deviceStatus": "online",
                    "batteryLevel": 78,
                    "signalStrength": 92,
                    "timestamp": format_datetime_for_firebase(current_time)
                }
            },
            "deviceInfo": {
                "type": "vitals_monitor",
                "manufacturer": "MedTech Systems",
                "model": "VM-2024",
                "roomId": "room_3",
                "bedId": "bed_4",
                "lastCalibrated": format_datetime_for_firebase(current_time - timedelta(days=12)),
                "calibrationDue": format_datetime_for_firebase(current_time + timedelta(days=18)),
                "maintenanceSchedule": format_datetime_for_firebase(current_time + timedelta(days=78))
            },
            "alerts": {
                "alert_6": {
                    "type": "info",
                    "message": "Battery level low - 78%",
                    "timestamp": format_datetime_for_firebase(current_time - timedelta(minutes=20)),
                    "resolved": False,
                    "assignedTo": "staff_3"
                }
            }
        },
        "monitor_4": {
            "vitals": {
                format_datetime_for_firebase(current_time): {
                    "heartRate": 78,
                    "oxygenLevel": 97,
                    "temperature": 36.9,
                    "bloodPressure": {
                        "systolic": 118,
                        "diastolic": 78
                    },
                    "respiratoryRate": 14,
                    "glucose": 88,
                    "bedOccupancy": False,
                    "patientId": "",
                    "deviceStatus": "online",
                    "batteryLevel": 65,
                    "signalStrength": 89,
                    "timestamp": format_datetime_for_firebase(current_time)
                }
            },
            "deviceInfo": {
                "type": "vitals_monitor",
                "manufacturer": "MedTech Systems",
                "model": "VM-2024",
                "roomId": "room_1",
                "bedId": "bed_2",
                "lastCalibrated": format_datetime_for_firebase(current_time - timedelta(days=5)),
                "calibrationDue": format_datetime_for_firebase(current_time + timedelta(days=25)),
                "maintenanceSchedule": format_datetime_for_firebase(current_time + timedelta(days=60))
            },
            "alerts": {
                "alert_7": {
                    "type": "info",
                    "message": "Device ready for next patient",
                    "timestamp": format_datetime_for_firebase(current_time - timedelta(hours=1)),
                    "resolved": True,
                    "resolvedBy": "staff_3",
                    "resolvedAt": format_datetime_for_firebase(current_time - timedelta(minutes=50))
                },
                "alert_8": {
                    "type": "warning",
                    "message": "Battery level getting low - 65%",
                    "timestamp": format_datetime_for_firebase(current_time - timedelta(minutes=30)),
                    "resolved": False,
                    "assignedTo": "staff_3"
                }
            }
        },
        "env_sensor_1": {
            "vitals": {
                format_datetime_for_firebase(current_time): {
                    "temperature": 22.5,
                    "humidity": 45,
                    "airQuality": 95,
                    "lightLevel": 80,
                    "noiseLevel": 35,
                    "pressure": 1013.25,
                    "co2Level": 400,
                    "deviceStatus": "online",
                    "batteryLevel": 88,
                    "signalStrength": 92,
                    "timestamp": format_datetime_for_firebase(current_time)
                },
                format_datetime_for_firebase(current_time - timedelta(minutes=15)): {
                    "temperature": 22.3,
                    "humidity": 44,
                    "airQuality": 94,
                    "lightLevel": 82,
                    "noiseLevel": 38,
                    "pressure": 1013.15,
                    "co2Level": 398,
                    "deviceStatus": "online",
                    "batteryLevel": 88,
                    "signalStrength": 91,
                    "timestamp": format_datetime_for_firebase(current_time - timedelta(minutes=15))
                }
            },
            "deviceInfo": {
                "type": "environmental_sensor",
                "manufacturer": "EnviroTech Solutions",
                "model": "ET-ENV-2024",
                "roomId": "room_1",
                "lastCalibrated": format_datetime_for_firebase(current_time - timedelta(days=30)),
                "calibrationDue": format_datetime_for_firebase(current_time + timedelta(days=60)),
                "maintenanceSchedule": format_datetime_for_firebase(current_time + timedelta(days=180))
            },
            "alerts": {}
        },
        "env_sensor_2": {
            "vitals": {
                format_datetime_for_firebase(current_time): {
                    "temperature": 23.0,
                    "humidity": 50,
                    "airQuality": 98,
                    "lightLevel": 75,
                    "noiseLevel": 30,
                    "pressure": 1013.30,
                    "co2Level": 380,
                    "deviceStatus": "online",
                    "batteryLevel": 92,
                    "signalStrength": 95,
                    "timestamp": format_datetime_for_firebase(current_time)
                },
                format_datetime_for_firebase(current_time - timedelta(minutes=15)): {
                    "temperature": 23.1,
                    "humidity": 49,
                    "airQuality": 97,
                    "lightLevel": 78,
                    "noiseLevel": 32,
                    "pressure": 1013.20,
                    "co2Level": 385,
                    "deviceStatus": "online",
                    "batteryLevel": 92,
                    "signalStrength": 94,
                    "timestamp": format_datetime_for_firebase(current_time - timedelta(minutes=15))
                }
            },
            "deviceInfo": {
                "type": "environmental_sensor",
                "manufacturer": "EnviroTech Solutions",
                "model": "ET-ENV-2024",
                "roomId": "room_2",
                "lastCalibrated": format_datetime_for_firebase(current_time - timedelta(days=25)),
                "calibrationDue": format_datetime_for_firebase(current_time + timedelta(days=65)),
                "maintenanceSchedule": format_datetime_for_firebase(current_time + timedelta(days=175))
            },
            "alerts": {}
        },
        "env_sensor_3": {
            "vitals": {
                format_datetime_for_firebase(current_time): {
                    "temperature": 21.0,
                    "humidity": 55,
                    "airQuality": 96,
                    "lightLevel": 85,
                    "noiseLevel": 40,
                    "pressure": 1013.10,
                    "co2Level": 420,
                    "deviceStatus": "online",
                    "batteryLevel": 76,
                    "signalStrength": 89,
                    "timestamp": format_datetime_for_firebase(current_time)
                },
                format_datetime_for_firebase(current_time - timedelta(minutes=15)): {
                    "temperature": 21.2,
                    "humidity": 54,
                    "airQuality": 95,
                    "lightLevel": 87,
                    "noiseLevel": 42,
                    "pressure": 1013.05,
                    "co2Level": 415,
                    "deviceStatus": "online",
                    "batteryLevel": 76,
                    "signalStrength": 88,
                    "timestamp": format_datetime_for_firebase(current_time - timedelta(minutes=15))
                }
            },
            "deviceInfo": {
                "type": "environmental_sensor",
                "manufacturer": "EnviroTech Solutions",
                "model": "ET-ENV-2024",
                "roomId": "room_3",
                "lastCalibrated": format_datetime_for_firebase(current_time - timedelta(days=20)),
                "calibrationDue": format_datetime_for_firebase(current_time + timedelta(days=70)),
                "maintenanceSchedule": format_datetime_for_firebase(current_time + timedelta(days=170))
            },
            "alerts": {
                "alert_9": {
                    "type": "warning",
                    "message": "CO2 levels slightly elevated - 420 ppm",
                    "timestamp": format_datetime_for_firebase(current_time - timedelta(minutes=10)),
                    "resolved": False,
                    "assignedTo": "staff_3"
                }
            }
        }
    }

    # Generate staff data
    staff_data = {
        "staff_1": {
            "personalInfo": {
                "name": "Dr. Sarah Chen",
                "role": "doctor",
                "department": "Cardiology",
                "specialization": "Cardiologist",
                "contact": {
                    "email": "sarah.chen@hospital.com",
                    "phone": "555-0101"
                }
            },
            "schedule": {
                current_time.date().isoformat(): {
                    "shiftStart": format_datetime_for_firebase(current_time - timedelta(hours=2)),
                    "shiftEnd": format_datetime_for_firebase(current_time + timedelta(hours=6)),
                    "ward": "Cardiology",
                    "roomIds": ["room_1", "room_3"],
                    "patientAssignments": ["patient_1", "patient_3"],
                    "shiftType": "day"
                }
            },
            "currentStatus": {
                "onDuty": True,
                "location": "room_1",
                "lastUpdated": format_datetime_for_firebase(current_time),
                "workload": 75,
                "lastBreak": format_datetime_for_firebase(current_time - timedelta(hours=1))
            },
            "performance": {
                "tasksCompleted": 45,
                "averageResponseTime": 8,
                "patientSatisfaction": 4.8
            }
        },
        "staff_2": {
            "personalInfo": {
                "name": "Nurse John Miller",
                "role": "nurse",
                "department": "Pulmonology",
                "specialization": "Respiratory Care",
                "contact": {
                    "email": "john.miller@hospital.com",
                    "phone": "555-0102"
                }
            },
            "schedule": {
                current_time.date().isoformat(): {
                    "shiftStart": format_datetime_for_firebase(current_time - timedelta(hours=4)),
                    "shiftEnd": format_datetime_for_firebase(current_time + timedelta(hours=4)),
                    "ward": "Pulmonology",
                    "roomIds": ["room_2"],
                    "patientAssignments": ["patient_2"],
                    "shiftType": "day"
                }
            },
            "currentStatus": {
                "onDuty": True,
                "location": "room_2",
                "lastUpdated": format_datetime_for_firebase(current_time),
                "workload": 60,
                "lastBreak": format_datetime_for_firebase(current_time - timedelta(minutes=30))
            },
            "performance": {
                "tasksCompleted": 85,
                "averageResponseTime": 5,
                "patientSatisfaction": 4.9
            }
        },
        "staff_3": {
            "personalInfo": {
                "name": "Tech Alex Wong",
                "role": "technician",
                "department": "Biomedical",
                "specialization": "Medical Equipment",
                "contact": {
                    "email": "alex.wong@hospital.com",
                    "phone": "555-0103"
                }
            },
            "schedule": {
                current_time.date().isoformat(): {
                    "shiftStart": format_datetime_for_firebase(current_time - timedelta(hours=3)),
                    "shiftEnd": format_datetime_for_firebase(current_time + timedelta(hours=5)),
                    "ward": "All",
                    "roomIds": ["room_1", "room_3", "room_2"],
                    "patientAssignments": [],
                    "shiftType": "day"
                }
            },
            "currentStatus": {
                "onDuty": True,
                "location": "room_3",
                "lastUpdated": format_datetime_for_firebase(current_time),
                "workload": 45,
                "lastBreak": format_datetime_for_firebase(current_time - timedelta(hours=2))
            },
            "performance": {
                "tasksCompleted": 12,
                "averageResponseTime": 15,
                "patientSatisfaction": 4.5
            }
        },
        "staff_4": {
            "personalInfo": {
                "name": "Nurse Emma Davis",
                "role": "nurse",
                "department": "Cardiology",
                "specialization": "Cardiac Care",
                "contact": {
                    "email": "emma.davis@hospital.com",
                    "phone": "555-0104"
                }
            },
            "schedule": {
                current_time.date().isoformat(): {
                    "shiftStart": format_datetime_for_firebase(current_time - timedelta(hours=2)),
                    "shiftEnd": format_datetime_for_firebase(current_time + timedelta(hours=6)),
                    "ward": "Cardiology",
                    "roomIds": ["room_1", "room_3"],
                    "patientAssignments": ["patient_1", "patient_3"],
                    "shiftType": "day"
                }
            },
            "currentStatus": {
                "onDuty": True,
                "location": "room_1",
                "lastUpdated": format_datetime_for_firebase(current_time),
                "workload": 80,
                "lastBreak": format_datetime_for_firebase(current_time - timedelta(minutes=45))
            },
            "performance": {
                "tasksCompleted": 65,
                "averageResponseTime": 4,
                "patientSatisfaction": 4.7
            }
        }
    }

    # Generate incidents data
    incidents_data = {
        "incident_1": {
            "type": "medical_emergency",
            "severity": "high",
            "description": "Patient experiencing severe chest pain",
            "location": {
                "roomId": "room_1",
                "bedId": "bed_1"
            },
            "timestamp": format_datetime_for_firebase(current_time - timedelta(hours=1)),
            "reportedBy": "staff_4",
            "involvedPatients": ["patient_1"],
            "status": "resolved",
            "assignedTo": "staff_1",
            "resolutionTime": 15,
            "resolvedAt": format_datetime_for_firebase(current_time - timedelta(minutes=45)),
            "notes": "Administered emergency medication, patient stabilized"
        },
        "incident_2": {
            "type": "equipment_failure",
            "severity": "medium",
            "description": "ECG Monitor malfunction",
            "location": {
                "roomId": "room_3",
                "bedId": "bed_4"
            },
            "timestamp": format_datetime_for_firebase(current_time - timedelta(minutes=30)),
            "reportedBy": "staff_3",
            "involvedPatients": ["patient_3"],
            "status": "in_progress",
            "assignedTo": "staff_3",
            "notes": "Technician working on repair"
        }
    }

    # Generate inventory data
    inventory_data = {
        "med_1": {
            "name": "Lisinopril",
            "category": "medication",
            "currentStock": 500,
            "minimumStock": 100,
            "unit": "tablets",
            "location": "pharmacy",
            "expiryDate": format_datetime_for_firebase(current_time + timedelta(days=180)),
            "supplier": "PharmaCorp",
            "cost": 0.5,
            "lastRestocked": format_datetime_for_firebase(current_time - timedelta(days=5))
        },
        "med_2": {
            "name": "Albuterol Inhaler",
            "category": "medication",
            "currentStock": 50,
            "minimumStock": 20,
            "unit": "inhalers",
            "location": "pharmacy",
            "expiryDate": format_datetime_for_firebase(current_time + timedelta(days=365)),
            "supplier": "RespiCare",
            "cost": 25.0,
            "lastRestocked": format_datetime_for_firebase(current_time - timedelta(days=10))
        },
        "sup_1": {
            "name": "N95 Masks",
            "category": "supplies",
            "currentStock": 1000,
            "minimumStock": 200,
            "unit": "pieces",
            "location": "storage",
            "expiryDate": format_datetime_for_firebase(current_time + timedelta(days=730)),
            "supplier": "MedSupply",
            "cost": 1.5,
            "lastRestocked": format_datetime_for_firebase(current_time - timedelta(days=2))
        },
        "equip_1": {
            "name": "Portable ECG",
            "category": "equipment",
            "currentStock": 5,
            "minimumStock": 2,
            "unit": "pieces",
            "location": "equipment_room",
            "expiryDate": format_datetime_for_firebase(current_time + timedelta(days=1825)),
            "supplier": "MedTech",
            "cost": 5000.0,
            "lastRestocked": format_datetime_for_firebase(current_time - timedelta(days=90))
        }
    }

    # Generate AI logs data
    ai_logs_data = {
        "log_1": {
            "modelId": "patient_risk_model",
            "patientId": "patient_1",
            "inputData": {
                "heartRate": 85,
                "oxygenLevel": 96,
                "temperature": 37.2,
                "bloodPressure": {
                    "systolic": 145,
                    "diastolic": 95
                },
                "respiratoryRate": 18,
                "contextData": {
                    "age": 65,
                    "conditions": ["hypertension", "diabetes"],
                    "medications": ["lisinopril", "metformin"]
                }
            },
            "output": {
                "riskLevel": "High",
                "riskScore": 75,
                "recommendations": [
                    "Increase blood pressure monitoring frequency",
                    "Review medication effectiveness"
                ],
                "alertTriggered": True
            },
            "timestamp": format_datetime_for_firebase(current_time - timedelta(minutes=15)),
            "processingTime": 0.45,
            "feedback": {
                "providedBy": "staff_1",
                "rating": 4,
                "comments": "Accurate prediction, helpful recommendations",
                "timestamp": format_datetime_for_firebase(current_time - timedelta(minutes=10))
            }
        }
    }

    # Generate system metrics data
    system_metrics_data = {
        format_datetime_for_firebase(current_time): {
            "totalPatients": 3,
            "criticalPatients": 1,
            "bedOccupancy": 75.0,
            "staffOnDuty": 4,
            "activeAlerts": 1,
            "systemUptime": 345600,
            "averageResponseTime": 250,
            "dataQuality": 98.5
        },
        format_datetime_for_firebase(current_time - timedelta(hours=1)): {
            "totalPatients": 3,
            "criticalPatients": 2,
            "bedOccupancy": 75.0,
            "staffOnDuty": 4,
            "activeAlerts": 2,
            "systemUptime": 342000,
            "averageResponseTime": 280,
            "dataQuality": 98.2
        }
    }

    return {
        "rooms": rooms_data,
        "beds": beds_data,
        "patients": patients_data,
        "staff": staff_data,
        "iotData": iot_data,
        "incidents": incidents_data,
        "inventory": inventory_data,
        "aiLogs": ai_logs_data,
        "systemMetrics": system_metrics_data
    } 