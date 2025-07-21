# Anomaly Detection Engine Documentation

## Overview

The Anomaly Detection Engine is a comprehensive system designed to detect sudden or abnormal fluctuations in patient vitals and room environment conditions that may indicate medical emergencies. It uses multiple machine learning approaches combined with rule-based detection to provide robust anomaly identification.

## Features

### Core Functionality
- **Real-time Anomaly Detection**: Processes incoming sensor data in real-time
- **Multi-Algorithm Approach**: Combines Isolation Forest, K-Means clustering, and rule-based detection
- **Severity Classification**: Categorizes anomalies by severity (LOW, MEDIUM, HIGH, CRITICAL)
- **Trend Analysis**: Detects concerning trends in recent readings
- **Automatic Alerts**: Generates alerts for medical staff when anomalies are detected

### Supported Metrics

#### Patient Vitals
- Heart Rate (bpm)
- Blood Pressure (Systolic/Diastolic mmHg)
- Body Temperature (°C)
- Oxygen Saturation (%)
- Respiratory Rate (breaths/min)
- Blood Glucose (mg/dL)

#### Environmental Conditions
- Room Temperature (°C)
- Humidity (%)
- Air Quality Index

## API Endpoints

### Anomaly Detection

#### `POST /anomalies/detect`
Detect anomalies in real-time sensor data.

**Request Body:**
```json
{
  "device_id": "string",
  "heart_rate": 75,
  "systolic_bp": 120,
  "diastolic_bp": 80,
  "temperature": 36.8,
  "oxygen_level": 97,
  "respiratory_rate": 16,
  "glucose": 100,
  "room_temperature": 22,
  "humidity": 50,
  "air_quality": 25
}
```

**Response:**
```json
{
  "device_id": "string",
  "timestamp": "2025-07-21T10:30:00.000Z",
  "is_anomaly": false,
  "anomaly_score": -0.123,
  "severity_level": "NORMAL",
  "severity_score": 0.5,
  "anomaly_type": [],
  "details": {},
  "trend_analysis": {
    "trend_anomaly": false,
    "trend_type": null
  }
}
```

### Data Retrieval

#### `GET /anomalies/{device_id}`
Get anomaly history for a specific device.

**Parameters:**
- `device_id`: Device identifier
- `hours`: Time window in hours (default: 24)

#### `GET /anomalies/`
Get all anomalies across all devices.

**Parameters:**
- `hours`: Time window in hours (default: 24)
- `severity_filter`: Filter by severity level (CRITICAL, HIGH, MEDIUM, LOW)

#### `GET /anomalies/alerts/active`
Get all active (unresolved) anomaly alerts.

#### `GET /anomalies/statistics`
Get anomaly detection statistics.

**Parameters:**
- `hours`: Time window in hours (default: 24)

### Alert Management

#### `PUT /anomalies/alerts/{device_id}/{alert_timestamp}/resolve`
Mark an alert as resolved.

### Model Management

#### `POST /anomalies/train`
Retrain anomaly detection models with recent data (background task).

## Anomaly Detection Algorithms

### 1. Isolation Forest
- **Type**: Unsupervised outlier detection
- **Use Case**: Detects statistical outliers in multi-dimensional data
- **Advantages**: Effective for high-dimensional data, no need for labeled data

### 2. K-Means Clustering
- **Type**: Distance-based anomaly detection
- **Use Case**: Identifies data points far from cluster centers
- **Advantages**: Good for detecting pattern deviations

### 3. Rule-Based Detection
- **Type**: Threshold-based detection
- **Use Case**: Immediate detection of values outside normal ranges
- **Advantages**: Fast, interpretable, medical knowledge-based

## Severity Classification

### Severity Levels

#### CRITICAL
- Values outside critical thresholds
- Multiple simultaneous violations
- Severity score > 8
- **Example**: Heart rate < 40 or > 120 bpm

#### HIGH
- Values outside normal thresholds
- Multiple violations or high anomaly score
- Severity score > 4
- **Example**: Heart rate < 60 or > 100 bpm with other violations

#### MEDIUM
- Single threshold violations
- Moderate anomaly scores
- Severity score > 2
- **Example**: Single vital sign outside normal range

#### LOW
- Minor deviations
- Low anomaly scores
- Severity score ≤ 2
- **Example**: Slight environmental variations

### Vital Sign Thresholds

| Vital Sign | Normal Range | Critical Range |
|------------|-------------|----------------|
| Heart Rate | 60-100 bpm | <40 or >120 bpm |
| Systolic BP | 90-140 mmHg | <70 or >180 mmHg |
| Diastolic BP | 60-90 mmHg | <40 or >110 mmHg |
| Temperature | 36.1-37.2°C | <35.0 or >39.0°C |
| Oxygen Level | 95-100% | <90% |
| Respiratory Rate | 12-20 /min | <8 or >30 /min |
| Blood Glucose | 70-140 mg/dL | <50 or >200 mg/dL |

## Integration with IoT System

The anomaly detection engine is automatically triggered when new vitals are posted through the IoT endpoints:

```
POST /iotData/{device_id}/vitals
```

This ensures real-time monitoring without requiring separate API calls for anomaly detection.

## Alert System

### Alert Generation
- Automatic alert creation when anomalies are detected
- Alerts stored in Firebase under `iotData/{device_id}/alerts/`
- Alert data includes severity, anomaly types, and detailed information

### Alert Management
- Alerts can be marked as resolved
- Active alerts can be retrieved for dashboard display
- Alerts include timestamps and device information

## Logging System

### Anomaly Logs
- All anomaly detection results are logged
- Stored in Firebase under `anomalies/{device_id}/`
- Includes detailed analysis and trend information

### Log Structure
```json
{
  "device_id": "string",
  "timestamp": "ISO timestamp",
  "is_anomaly": boolean,
  "anomaly_score": number,
  "severity_level": "string",
  "anomaly_type": ["string"],
  "details": {},
  "trend_analysis": {}
}
```

## Training and Model Management

### Initial Training
- Models can be trained with historical data
- Synthetic data generation for initial setup
- Minimum 50 samples recommended for training

### Continuous Learning
- Models can be retrained with recent data
- Background retraining to avoid service disruption
- Automatic model persistence

### Model Files
- Models saved in `models/anomaly_detection_models.pkl`
- Includes all trained components and thresholds
- Automatic loading on service startup

## Configuration

### Thresholds
Thresholds can be customized in the `AnomalyDetectionEngine` class:

```python
self.vital_thresholds = {
    'heart_rate': {'low': 60, 'high': 100, 'critical_low': 40, 'critical_high': 120},
    # ... other thresholds
}
```

### Model Parameters
- `contamination`: Expected proportion of outliers (default: 0.1)
- `n_clusters`: Number of clusters for K-Means (default: 3)
- `n_estimators`: Number of trees in Isolation Forest (default: 100)

## Testing

### Test Script
Use the provided test script to validate functionality:

```bash
python test_anomaly_detection.py
```

### Test Categories
1. **Normal Vitals**: Verify no false positives
2. **Abnormal Vitals**: Verify detection of anomalies
3. **Critical Vitals**: Verify high-severity detection
4. **IoT Integration**: Test automatic detection
5. **Continuous Testing**: Extended monitoring simulation

## Deployment Considerations

### Performance
- Background processing prevents API blocking
- Efficient data structures for real-time processing
- Configurable data retention limits

### Scalability
- Stateless design for horizontal scaling
- Firebase integration for distributed storage
- Efficient memory management

### Reliability
- Error handling and logging
- Graceful degradation if models unavailable
- Rule-based fallback detection

## Future Enhancements

### Planned Features
1. **Custom Thresholds**: Per-patient threshold customization
2. **Advanced ML Models**: Deep learning approaches (Autoencoders)
3. **Correlation Analysis**: Multi-device anomaly correlation
4. **Predictive Alerts**: Early warning system
5. **Integration APIs**: Third-party system integration

### Model Improvements
1. **Online Learning**: Real-time model updates
2. **Ensemble Methods**: Combining multiple algorithms
3. **Time Series Analysis**: LSTM-based trend detection
4. **Contextual Analysis**: Patient history consideration
