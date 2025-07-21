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
                "lightLevel": 80,
                "noiseLevel": 35,
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
            "modelId": "decisionTree",
            "modelVersion": "1.2.0",
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
        },
        "log_2": {
            "modelId": "lstm",
            "modelVersion": "2.1.0",
            "patientId": "patient_2",
            "inputData": {
                "heartRate": 90,
                "oxygenLevel": 92,
                "temperature": 37.8,
                "bloodPressure": {
                    "systolic": 125,
                    "diastolic": 82
                },
                "respiratoryRate": 22,
                "contextData": {
                    "age": 45,
                    "conditions": ["asthma", "copd"],
                    "medications": ["albuterol"]
                }
            },
            "output": {
                "riskLevel": "Moderate",
                "riskScore": 45,
                "cluster": 2,
                "recommendations": [
                    "Monitor respiratory rate closely",
                    "Consider supplemental oxygen"
                ],
                "alertTriggered": False
            },
            "timestamp": format_datetime_for_firebase(current_time),
            "processingTime": 0.65,
            "feedback": {
                "providedBy": "staff_2",
                "rating": 5,
                "comments": "Early warning helped prevent exacerbation",
                "timestamp": format_datetime_for_firebase(current_time + timedelta(minutes=5))
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
        "staff": staff_data,
        "incidents": incidents_data,
        "inventory": inventory_data,
        "aiLogs": ai_logs_data,
        "systemMetrics": system_metrics_data
    } 