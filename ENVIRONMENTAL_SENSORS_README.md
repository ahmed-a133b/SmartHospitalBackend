# Environmental Sensors Data Setup

This script initializes environmental sensor data in your Smart Hospital Firebase database.

## Features

### 🌡️ Complete Environmental Monitoring
- **Temperature**: Room temperature monitoring (18-26°C range)
- **Humidity**: Relative humidity levels (30-60% range)
- **Air Quality Index**: Air quality measurements (90-100 range)
- **Light Level**: Ambient light monitoring (60-100% range)
- **Noise Level**: Sound level monitoring (20-55 dB range)
- **Atmospheric Pressure**: Barometric pressure (1011-1016 hPa range)
- **CO2 Level**: Carbon dioxide concentration (300-500 ppm range)

### 🏥 Room-Specific Configurations
All sensors now use **general room configuration** for consistent monitoring:
- **Temperature**: 20.0-26.0°C (comfortable range)
- **Humidity**: 40-60% (optimal humidity)
- **Air Quality Index**: 90-98 (good quality)
- **Light Level**: 75-95% (adequate lighting)
- **Noise Level**: 30-50 dB (normal environment)
- **Atmospheric Pressure**: 1011.0-1016.0 hPa (standard range)
- **CO2 Level**: 380-500 ppm (acceptable levels)

### 📊 Historical Data
- Generates 24 hours of historical readings
- Multiple readings per sensor at different time intervals
- Realistic data progression and variations

## Setup Instructions

### Prerequisites
1. **Python Environment**: Ensure Python 3.7+ is installed
2. **Dependencies**: Install required packages
   ```bash
   pip install -r requirements.txt
   ```
3. **Firebase Configuration**: Set up your `.env` file with Firebase credentials

### Quick Setup (Windows)
```bash
setup_env_sensors.bat
```

### Manual Setup
```bash
python add_env_sensors.py
```

## Generated Data Structure

### Environmental Sensors
The script creates 5 environmental sensors:

| Sensor ID | Room ID |
|-----------|---------|
| env_sensor_1 | room_1 |
| env_sensor_2 | room_2 |
| env_sensor_3 | room_3 |
| env_sensor_4 | room_4 |
| env_sensor_5 | room_5 |

### Data Format
Each sensor includes:
```json
{
  "vitals": {
    "timestamp": {
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
      "timestamp": "2025-07-29_14-30-00"
    }
  },
  "deviceInfo": {
    "type": "environmental_sensor",
    "manufacturer": "EnviroTech Solutions",
    "model": "ET-ENV-2024",
    "roomId": "room_1",
    "lastCalibrated": "2025-07-14_14-30-00",
    "calibrationDue": "2025-10-12_14-30-00",
    "maintenanceSchedule": "2026-01-25_14-30-00",
    "installationDate": "2024-07-29_14-30-00"
  },
  "alerts": {
    "2025-07-29_13-45-00": {
      "type": "warning",
      "message": "CO2 levels slightly elevated - 480 ppm",
      "timestamp": "2025-07-29_13-45-00",
      "resolved": true,
      "resolvedBy": "staff_2",
      "resolvedAt": "2025-07-29_14-00-00",
      "category": "environmental"
    }
  }
}
```

## Environmental Parameters

All sensors use the **general room configuration** with these ranges:

- **Temperature**: 20.0-26.0°C (comfortable range)
- **Humidity**: 40-60% (optimal humidity)
- **Air Quality**: 90-98 (good quality)
- **Light Level**: 75-95% (adequate lighting)
- **Noise Level**: 30-50 dB (normal environment)
- **Pressure**: 1011.0-1016.0 hPa (standard atmospheric pressure)
- **CO2**: 380-500 ppm (acceptable levels)

## Integration with Anomaly Detection

This environmental data is designed to work with the enhanced anomaly detection system that includes:
- Environmental anomaly detection
- Combined medical + environmental monitoring
- Alert generation for environmental hazards
- Comprehensive 14-feature model training

## Troubleshooting

### Common Issues
1. **Firebase Connection Error**: Check your `.env` file configuration
2. **Permission Denied**: Ensure your Firebase service account has write permissions
3. **Module Not Found**: Run `pip install -r requirements.txt`

### Environment Variables Required
```
FIREBASE_KEY_JSON={"type": "service_account", ...}
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com/
```

## Next Steps

After running this script:
1. ✅ Environmental sensors are active in your database
2. 🔄 Train your anomaly detection model with: `python train_anomaly.py`
3. 📊 View environmental data in your dashboard
4. ⚠️ Monitor environmental alerts and thresholds

## Support

For issues or questions about environmental sensor setup, check:
- Firebase console for data verification
- Application logs for connection issues
- Dashboard for real-time environmental monitoring
