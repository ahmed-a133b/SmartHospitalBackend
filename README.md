# 🏥 Smart Hospital Backend

A comprehensive healthcare management system backend built with FastAPI, featuring real-time patient monitoring, anomaly detection, and predictive analytics for smart hospital operations.

## 🌟 Features

### Core Functionality
- **Patient Management**: Complete patient lifecycle management with medical records
- **Real-time IoT Monitoring**: Live vital signs monitoring from connected medical devices
- **Anomaly Detection**: AI-powered anomaly detection using Isolation Forest algorithms
- **Predictive Analytics**: Patient risk assessment and outcome prediction
- **Alert System**: Real-time alerts for critical patient conditions
- **Staff Management**: Healthcare staff scheduling and assignment
- **Room & Bed Management**: Hospital resource allocation and tracking
- **Data Simulation**: Realistic medical data generation for testing and development

### AI/ML Capabilities
- **Isolation Forest Model**: Detects anomalies in patient vital signs
- **Patient Risk Prediction**: Machine learning models for risk assessment
- **Real-time Analytics**: Statistical analysis of patient data trends
- **Automated Alerting**: Smart alert generation based on severity levels

## 🏗️ Architecture

```
smart_hospital_backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── firebase_config.py      # Firebase Realtime Database configuration
│   ├── routers/                # API endpoint modules
│   │   ├── patients.py         # Patient management endpoints
│   │   ├── anomalies.py        # Anomaly detection endpoints
│   │   ├── predictions.py      # ML prediction endpoints
│   │   ├── iot.py             # IoT device management
│   │   ├── alerts.py          # Alert system endpoints
│   │   ├── staff.py           # Staff management
│   │   ├── rooms.py           # Room management
│   │   ├── beds.py            # Bed allocation
│   │   └── simulation.py      # Data simulation endpoints
│   ├── vitals_simulator.py    # Realistic vital signs simulation
│   └── data_simulation.py     # Medical data generation
├── models/                    # Trained ML models
│   ├── isolation_forest_anomaly_model.pkl
│   └── patient_risk_model.pkl
├── train_anomaly.py          # Anomaly detection model training
├── train_patient_risk.py     # Risk prediction model training
└── init_iot_data.py         # IoT device initialization
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Firebase Realtime Database account
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ahmed-a133b/SmartHospitalBackend.git
   cd smart_hospital_backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Firebase**
   - Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
   - Generate a service account key (JSON file)
   - Create `.env` file in the root directory:
   ```env
   FIREBASE_CREDENTIALS_PATH=path/to/your/firebase-credentials.json
   FIREBASE_DATABASE_URL=https://your-project.firebaseio.com/
   ```

5. **Initialize the database**
   ```bash
   python init_iot_data.py
   ```

6. **Start the server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

The API will be available at `http://localhost:8000`

## 📖 API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

#### Patient Management
- `GET /patients/` - List all patients
- `POST /patients/` - Create new patient
- `GET /patients/{patient_id}` - Get patient details
- `PUT /patients/{patient_id}` - Update patient information
- `DELETE /patients/{patient_id}` - Remove patient

#### IoT & Monitoring
- `POST /iot/vitals/{monitor_id}` - Submit vital signs data
- `GET /iot/devices/` - List all IoT devices
- `GET /iot/vitals/{patient_id}` - Get patient vital history

#### Anomaly Detection
- `GET /anomalies/detect/{monitor_id}` - Detect anomalies for specific monitor
- `GET /anomalies/{device_id}` - Get anomaly history for device
- `GET /anomalies/alerts/active` - Get active alerts
- `GET /anomalies/model/status` - Check ML model status

#### Predictions
- `POST /predict/risk/{patient_id}` - Predict patient risk level
- `GET /predict/trends/{patient_id}` - Get patient health trends

#### Data Simulation
- `POST /simulation/start/{monitor_id}` - Start realistic data simulation
- `POST /simulation/stop/{monitor_id}` - Stop data simulation
- `GET /simulation/status` - Check simulation status

## 🤖 Machine Learning Models

### Anomaly Detection Model
- **Algorithm**: Isolation Forest
- **Purpose**: Detect abnormal vital signs patterns
- **Features**: Heart rate, blood pressure, temperature, oxygen saturation
- **Training**: Automated retraining with new data

### Patient Risk Prediction Model
- **Algorithm**: Ensemble methods (Random Forest/Gradient Boosting)
- **Purpose**: Predict patient deterioration risk
- **Features**: Vital signs, medical history, demographics
- **Output**: Risk score and severity level

### Model Training
```bash
# Train anomaly detection model
python train_anomaly.py

# Train patient risk model
python train_patient_risk.py
```

## 📊 Database Schema

The system uses Firebase Realtime Database with the following structure:

```json
{
  "patients": {
    "patient_1": {
      "personalInfo": {...},
      "medicalHistory": {...},
      "currentStatus": {...}
    }
  },
  "iotData": {
    "monitor_1": {
      "deviceInfo": {...},
      "vitals": {
        "patient_1": {
          "timestamp": {
            "heartRate": 72,
            "bloodPressureSystolic": 120,
            "bloodPressureDiastolic": 80,
            "temperature": 98.6,
            "oxygenSaturation": 98
          }
        }
      },
      "alerts": {...}
    }
  },
  "anomalies": {...},
  "staff": {...},
  "rooms": {...}
}
```

For detailed schema documentation, see [smart_hospital_schema.md](smart_hospital_schema.md).

## 🔧 Configuration

### Environment Variables
```env
# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=path/to/firebase-key.json
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com/

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG_MODE=True

# ML Model Configuration
MODEL_UPDATE_INTERVAL=3600  # seconds
ANOMALY_THRESHOLD=0.3
```

### CORS Configuration
The API is configured to allow requests from:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (React dev server)
- `http://localhost:4173` (Vite preview)

## 🧪 Data Simulation

The system includes comprehensive data simulation capabilities:

```python
# Start simulation for a monitor
POST /simulation/start/monitor_1
{
  "patientId": "patient_1",
  "duration": 3600,  # seconds
  "anomalyProbability": 0.1
}
```

Features:
- Realistic vital signs generation
- Configurable anomaly injection
- Patient-specific patterns
- Real-time data streaming

## 🚨 Alert System

### Alert Severity Levels
- **CRITICAL**: Immediate intervention required
- **HIGH**: Urgent attention needed
- **MEDIUM**: Monitor closely
- **LOW**: Note for review

### Alert Types
- Vital signs anomalies
- Equipment malfunctions
- Patient deterioration predictions
- System status alerts

## 🔒 Security

- **Input Validation**: Pydantic models for all API inputs
- **Firebase Security**: Secure database access with service accounts
- **CORS Protection**: Configured for specific frontend origins
- **Error Handling**: Comprehensive error handling and logging

## 🧪 Testing

```bash
# Run the application in development mode
uvicorn app.main:app --reload

# Test API endpoints
curl http://localhost:8000/patients/
curl http://localhost:8000/anomalies/model/status
```

## 📈 Monitoring & Logging

- **Logging**: Comprehensive logging throughout the application
- **Error Tracking**: Detailed error messages and stack traces
- **Performance Monitoring**: Request/response time tracking
- **Health Checks**: System status endpoints

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add comprehensive docstrings
- Include unit tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI**: Modern, fast web framework for building APIs
- **Firebase**: Real-time database and authentication
- **Scikit-learn**: Machine learning algorithms
- **Uvicorn**: Lightning-fast ASGI server

## 📞 Support

For support, please open an issue on GitHub or contact the development team.

---

**Built with ❤️ for better healthcare management**
