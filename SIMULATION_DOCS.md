# Enhanced IoT Device Simulation Documentation

## Overview

The Enhanced IoT Device Simulation system provides comprehensive real-time simulation of medical IoT devices for smart hospital systems. It generates realistic data streams with sophisticated anomaly detection, health risk scenarios, and environmental hazards to thoroughly test your web dashboard and digital twin applications.

## Features

### 🏥 Medical Device Simulation

#### Vital Signs Monitoring
- **Heart Rate**: Natural variation with arrhythmia detection
- **Blood Pressure**: Systolic/diastolic with hypertensive/hypotensive events
- **Oxygen Saturation**: SpO2 levels with hypoxemia scenarios
- **Body Temperature**: Fever spikes and hypothermia detection
- **Respiratory Rate**: Breathing patterns with distress simulation
- **Blood Glucose**: Diabetic emergency scenarios (hyper/hypoglycemia)

#### Patient Profile Integration
- Age-based baseline adjustments
- Medical condition-specific variations
- Medication interaction effects
- Risk factor multipliers
- Current patient state influence

### 🚨 Anomaly Generation System

#### Cardiac Anomalies
- **Cardiac Arrhythmia**: Irregular heart rhythms with high variability
- **Tachycardia**: Elevated heart rate (>150 bpm)
- **Bradycardia**: Slow heart rate (<50 bpm)
- **Hypertensive Crisis**: Dangerously high blood pressure (>180/110)
- **Hypotensive Shock**: Critical low blood pressure (<80/60)

#### Respiratory Anomalies
- **Respiratory Distress**: Elevated respiratory rate with desaturation
- **Hypoxemia**: Low blood oxygen levels (<88% SpO2)
- **Acute Respiratory Failure**: Progressive oxygen decline

#### Metabolic Anomalies
- **Hyperglycemia**: High blood sugar (>300 mg/dL)
- **Hypoglycemia**: Low blood sugar (<60 mg/dL)
- **Diabetic Ketoacidosis**: Severe diabetic emergency

#### Thermal Anomalies
- **Fever Spike**: High body temperature (>39.5°C)
- **Hypothermia**: Low body temperature (<35°C)
- **Sepsis Progression**: Infection-related temperature changes

### 🌡️ Environmental Monitoring

#### Sensor Types
- **Temperature Control**: Room temperature monitoring (18-28°C range)
- **Humidity Management**: Relative humidity tracking (30-70% range)
- **Air Quality**: Air quality index and particulate monitoring
- **Noise Levels**: Ambient sound monitoring for patient comfort
- **CO2 Levels**: Carbon dioxide concentration tracking
- **Light Levels**: Illumination monitoring

#### Environmental Hazards
- **Temperature Extremes**: Hot/cold room conditions
- **Humidity Extremes**: Too dry or too humid conditions
- **Poor Air Quality**: Low air quality index or high particulates
- **Excessive Noise**: Disruptive noise levels
- **Contamination Risk**: Airborne contamination detection

### 🔔 Intelligent Alerting System

#### Alert Levels
- **CRITICAL**: Immediate life-threatening conditions
- **HIGH**: Urgent medical attention required
- **MEDIUM**: Prompt medical review needed
- **LOW**: Monitoring and documentation required

#### Alert Components
- Unique alert ID and timestamp
- Device and patient identification
- Anomaly type classification
- Vital sign values at time of alert
- Environmental conditions (if applicable)
- Clinical recommendations
- Escalation rules

### 📊 Real-time Analytics

#### Statistics Dashboard
- Total alert counts by severity
- Anomaly type distribution
- Device performance metrics
- Patient alert frequency
- Time-based trend analysis

#### Monitoring Capabilities
- Live simulation status
- Real-time alert streaming
- Performance metrics
- Historical data analysis

## API Endpoints

### Simulation Control
```
POST /simulation/start          # Start enhanced simulation
POST /simulation/stop           # Stop simulation gracefully
POST /simulation/restart        # Restart simulation
GET  /simulation/status         # Get current simulation status
GET  /simulation/logs          # Get simulation logs
```

### Alert Management
```
GET  /simulation/alerts/recent          # Get recent alerts
GET  /simulation/alerts/critical        # Get critical alerts (24h)
GET  /simulation/statistics            # Get comprehensive statistics
```

### Testing & Development
```
POST /simulation/trigger-anomaly       # Manually trigger specific anomaly
GET  /simulation/anomaly-types        # Get available anomaly types
```

## Configuration

### Anomaly Probabilities
Configurable base probabilities for each anomaly type:
- Cardiac events: 1-3% per cycle
- Respiratory issues: 2-2.5% per cycle
- Metabolic disorders: 1.5-2.5% per cycle
- Environmental hazards: 0.5-2% per cycle

### Risk Factor Multipliers
- **Elderly patients (>70)**: 1.5x increased risk
- **Cardiac conditions**: 3x cardiac event risk
- **Diabetes**: 5x hyperglycemia, 3x hypoglycemia risk
- **Respiratory conditions**: 4x respiratory distress risk
- **Critical condition**: 2x overall risk

### Alert Thresholds
#### Critical Thresholds
- Heart Rate: <50 or >180 bpm
- Blood Pressure: <80/60 or >180/110 mmHg
- Oxygen Level: <80%
- Temperature: <35°C or >39.5°C
- Glucose: <50 or >400 mg/dL

## Usage Examples

### Starting the Simulation
```python
import requests

# Start simulation
response = requests.post("http://localhost:8000/simulation/start")
result = response.json()
print(f"Simulation started: {result['success']}")
```

### Monitoring Alerts
```python
# Get recent alerts
response = requests.get("http://localhost:8000/simulation/alerts/recent?limit=10")
alerts = response.json()['alerts']

for alert in alerts:
    print(f"{alert['alertLevel']}: {alert['message']}")
```

### Triggering Test Anomalies
```python
# Trigger cardiac arrhythmia
payload = {
    "deviceId": "monitor_001",
    "anomalyType": "cardiac_arrhythmia",
    "severity": 0.8
}
response = requests.post("http://localhost:8000/simulation/trigger-anomaly", json=payload)
```

## Integration with Digital Twin and VR

### Data Stream Format
The simulation outputs standardized JSON data streams compatible with:
- **Web Dashboards**: Real-time vital sign displays
- **Unity Digital Twin**: 3D hospital environment visualization
- **VR Applications**: Immersive medical training scenarios

### Real-time Updates
- 5-second update intervals for vital signs
- Immediate alert notifications
- Continuous environmental monitoring
- WebSocket support for live data streaming

### Example Data Structure
```json
{
  "timestamp": "2025-01-23_14:30:15",
  "deviceId": "monitor_001",
  "patientId": "patient_123",
  "vitals": {
    "heartRate": 95,
    "bloodPressure": {"systolic": 140, "diastolic": 90},
    "oxygenLevel": 96,
    "temperature": 37.2,
    "respiratoryRate": 18,
    "glucose": 120
  },
  "deviceStatus": "online",
  "batteryLevel": 87,
  "signalStrength": 92
}
```

## Testing Scenarios

### Medical Emergency Simulations
1. **Cardiac Event Progression**: Gradual onset arrhythmia leading to crisis
2. **Respiratory Failure**: Progressive hypoxemia with increasing distress
3. **Diabetic Emergency**: Rapid glucose changes with ketoacidosis risk
4. **Sepsis Development**: Fever, tachycardia, and hypotension progression
5. **Post-operative Complications**: Wound infection with vital sign changes

### Environmental Challenge Scenarios
1. **HVAC Failure**: Temperature extremes affecting patient comfort
2. **Air Quality Issues**: Poor ventilation with CO2 buildup
3. **Noise Disturbances**: Excessive ambient noise affecting recovery
4. **Humidity Problems**: Too dry or humid conditions
5. **Contamination Events**: Airborne particle increases

### System Stress Testing
1. **Multiple Simultaneous Alerts**: Testing alert handling capacity
2. **Cascading Failures**: Environmental issues affecting multiple patients
3. **High-frequency Anomalies**: Rapid succession of medical events
4. **Network Simulation**: Testing with connectivity issues
5. **Battery Management**: Low power scenario simulations

## Best Practices

### Deployment
- Use proper environment variables for Firebase configuration
- Monitor system resources during extended simulation runs
- Implement proper logging for debugging and analysis
- Set up alert thresholds appropriate for your testing needs

### Testing
- Start with low anomaly probabilities for initial testing
- Gradually increase complexity as system stability is confirmed
- Use manual anomaly triggers for specific scenario testing
- Monitor both medical and environmental data streams

### Development
- Implement proper error handling for network issues
- Cache patient profiles for performance optimization
- Use background tasks for non-blocking simulation execution
- Implement graceful shutdown for clean termination

## Technical Requirements

### Dependencies
- Python 3.8+
- FastAPI framework
- Firebase Admin SDK
- Pydantic for data validation
- Asyncio for concurrent operations

### System Resources
- Minimum 2GB RAM for stable operation
- Network connectivity for Firebase integration
- CPU: 2+ cores recommended for multiple device simulation
- Storage: 1GB+ for logs and temporary data

### Firebase Configuration
- Realtime Database with appropriate security rules
- Service account with read/write permissions
- Proper indexing for alert queries
- Backup strategy for critical simulation data

## Troubleshooting

### Common Issues
1. **Firebase Connection Errors**: Check environment variables and network
2. **High Memory Usage**: Reduce simulation frequency or device count
3. **Missing Patient Data**: Ensure patient profiles exist in database
4. **Alert Overload**: Adjust anomaly probabilities in configuration
5. **Performance Issues**: Monitor system resources and optimize queries

### Debug Mode
Enable detailed logging for troubleshooting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This enhanced simulation system provides a comprehensive testing environment for your smart hospital IoT infrastructure, ensuring robust performance under realistic medical scenarios and emergency conditions.
