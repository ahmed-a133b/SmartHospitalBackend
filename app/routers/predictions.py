from fastapi import APIRouter
from pydantic import BaseModel
import joblib
import numpy as np

router = APIRouter(prefix="/predict", tags=["Predictions"])

#model = joblib.load("models/risk_model.pkl") 

class Vitals(BaseModel):
    heartRate: float
    oxygenLevel: float
    temperature: float
    systolic: float
    diastolic: float
    age: int = 50 

@router.post("/")
def predict_risk(vitals: Vitals):
    features = [[
        vitals.heartRate, vitals.oxygenLevel, vitals.temperature,
        vitals.systolic, vitals.diastolic, vitals.age
    ]]
    #prediction = model.predict(features)[0]
    return {"riskLevel": "No prediction"}
