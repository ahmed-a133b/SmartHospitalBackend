from fastapi import FastAPI
from app.routers import patients, predictions, alerts, staff, iot, anomalies
from app.firebase_config import init_firebase
from fastapi.middleware.cors import CORSMiddleware
from app.routers import realtime


app = FastAPI(title="Smart Hospital API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # React dev server (if needed)
        "http://127.0.0.1:5173",  # Alternative Vite URL
        "http://localhost:4173",  # Vite preview
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods including OPTIONS
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Methods",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Credentials",
    ],
    expose_headers=["*"],  # Expose all headers
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Initialize Firebase
init_firebase()

# Include routers
app.include_router(patients.router)
app.include_router(predictions.router)
app.include_router(alerts.router)
app.include_router(staff.router)
app.include_router(iot.router)
app.include_router(anomalies.router)
#app.include_router(realtime.router)

