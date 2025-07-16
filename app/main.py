from fastapi import FastAPI
from routers import patients, predictions, alerts, staff, iot
from firebase_config import init_firebase
from fastapi.middleware.cors import CORSMiddleware
from routers import realtime


app = FastAPI(title="Smart Hospital API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",           
        "https://your-web-dashboard.com",  
        "http://192.168.0.101:5500",       
    ],
    allow_credentials=True,                # Allows cookies and auth headers
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"]
)


init_firebase()

app.include_router(patients.router)
#app.include_router(predictions.router)
app.include_router(alerts.router)
app.include_router(staff.router)
app.include_router(iot.router)
#app.include_router(realtime.router)

