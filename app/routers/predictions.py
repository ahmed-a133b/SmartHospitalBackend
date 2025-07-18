from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import pandas as pd
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
        
        # Getting class names
        class_names = model.named_steps['classifier'].classes_
        prob_dict = {class_name: float(prob) for class_name, prob in zip(class_names, probabilities)}
        
        return {
            "prediction": prediction,
            "probabilities": prob_dict
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")