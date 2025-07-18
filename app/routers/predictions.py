from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.firebase_config import get_ref
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

router = APIRouter(prefix="/predict", tags=["Predictions"])

# Loading the trained model
model = joblib.load("models/patient_risk_model.pkl")

class Vitals(BaseModel):
    heartRate: float
    oxygenLevel: float
    temperature: float
    systolic: float
    diastolic: float
    age: int = 50
    glucose: float = 100.0  # Default value based on dataset mean
    respiratoryRate: float = 16.0  # Default value based on dataset mean
    numConditions: int = 0  # Default to 0 conditions
    conditions: str = ""  # Default to empty string for no conditions
    patient_id: str = "" #Patient ID

@router.post("/risk")
def predict_risk(vitals: Vitals):
    try:
        # Converting input data to DataFrame to match model training format
        features = pd.DataFrame([{
            "heart_rate": vitals.heartRate,
            "oxygen_level": vitals.oxygenLevel,
            "temperature": vitals.temperature,
            "systolic_bp": vitals.systolic,
            "diastolic_bp": vitals.diastolic,
            "age": vitals.age,
            "glucose": vitals.glucose,
            "respiratory_rate": vitals.respiratoryRate,
            "num_conditions": vitals.numConditions,
            "conditions": vitals.conditions
        }])
        
        # Making prediction
        prediction = model.predict(features)[0]
        probabilities = model.predict_proba(features)[0]
        max_prob = float(np.max(probabilities))

        # Getting class names
        class_names = model.named_steps['classifier'].classes_
        prob_dict = {class_name: float(prob) for class_name, prob in zip(class_names, probabilities)}

        # Convert conditions string to list
        conditions_list = vitals.conditions.split("|") if vitals.conditions else []
        
        # Fetch existing patient data
        patient_ref = get_ref(f"patients/{vitals.patient_id}/predictions/default_model")
        patient_data = patient_ref.get()
        if not patient_data:
            raise HTTPException(status_code=404, detail=f"Patient {vitals.patient_id} not found")
        
        #Update predictions field
        patient_data = {
            'riskLevel': prediction,
            'riskScore': max_prob,
            'confidence': max_prob,
            'predictedAt': datetime.now().isoformat(),
            'nextPrediction': (datetime.now() + timedelta(hours=24)).isoformat(),
            'factors': conditions_list
        }
        
        #Save updated patient data
        patient_ref.set(patient_data)
        
        return {
            "prediction": prediction,
            "probabilities": prob_dict,
            "patient_id": vitals.patient_id,
            "updated_risk_level": patient_data
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")