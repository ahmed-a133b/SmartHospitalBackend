"""
Training script for Anomaly Detection using Isolation Forest
This script trains a single Isolation Forest model and saves it to the models folder
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import random
import os

def generate_synthetic_training_data(num_samples=500):
    """
    Generate synthetic training data for anomaly detection
    This creates realistic vital signs data with some normal variations
    """
    training_data = []
    
    for i in range(num_samples):
        # Generate normal vital signs with realistic variations
        data_point = {
            'heart_rate': np.random.normal(75, 10),  # Normal: 60-100
            'systolic_bp': np.random.normal(120, 15),  # Normal: 90-140
            'diastolic_bp': np.random.normal(80, 10),  # Normal: 60-90
            'temperature': np.random.normal(36.8, 0.3),  # Normal: 36.1-37.2
            'oxygen_level': np.random.normal(97, 2),  # Normal: 95-100
            'respiratory_rate': np.random.normal(16, 3),  # Normal: 12-20
            'glucose': np.random.normal(100, 20),  # Normal: 70-140
            'room_temperature': np.random.normal(22, 2),  # Normal: 20-24
            'humidity': np.random.normal(50, 8),  # Normal: 40-60
            'air_quality': np.random.normal(25, 15)  # Normal: 0-50
        }
        
        # Ensure values are within realistic bounds
        data_point['heart_rate'] = max(50, min(110, data_point['heart_rate']))
        data_point['systolic_bp'] = max(80, min(150, data_point['systolic_bp']))
        data_point['diastolic_bp'] = max(50, min(100, data_point['diastolic_bp']))
        data_point['temperature'] = max(35.5, min(38.0, data_point['temperature']))
        data_point['oxygen_level'] = max(90, min(100, data_point['oxygen_level']))
        data_point['respiratory_rate'] = max(10, min(25, data_point['respiratory_rate']))
        data_point['glucose'] = max(60, min(180, data_point['glucose']))
        data_point['room_temperature'] = max(18, min(26, data_point['room_temperature']))
        data_point['humidity'] = max(30, min(70, data_point['humidity']))
        data_point['air_quality'] = max(0, min(80, data_point['air_quality']))
        
        training_data.append(data_point)
    
    return training_data

def prepare_features(data_list):
    """
    Convert list of data dictionaries to feature matrix
    """
    feature_names = ['heart_rate', 'systolic_bp', 'diastolic_bp', 'temperature', 
                    'oxygen_level', 'respiratory_rate', 'glucose', 'room_temperature', 
                    'humidity', 'air_quality']
    
    features = []
    for data_point in data_list:
        row = [data_point.get(feature, 0) for feature in feature_names]
        features.append(row)
    
    return np.array(features), feature_names

def train_isolation_forest_model():
    """
    Train Isolation Forest model and save to models folder
    """
    print("Starting Isolation Forest model training...")
    
    # Generate synthetic training data
    training_data = generate_synthetic_training_data(500)
    print(f"Generated {len(training_data)} synthetic data points")
    
    # Prepare features
    X_train, feature_names = prepare_features(training_data)
    print(f"Feature matrix shape: {X_train.shape}")
    print(f"Features: {feature_names}")
    
    # Initialize and fit scaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)
    print("Data normalized using StandardScaler")
    
    # Initialize and train Isolation Forest
    isolation_forest = IsolationForest(
        contamination=0.1,  # Expected proportion of outliers
        random_state=42,
        n_estimators=100,
        max_samples='auto',
        max_features=1.0
    )
    
    print("Training Isolation Forest...")
    isolation_forest.fit(X_scaled)
    print("Training completed!")
    
    # Save model and scaler (following patient risk model approach)
    model_data = {
        'model': isolation_forest,
        'scaler': scaler,
        'feature_names': feature_names,
        'training_samples': len(training_data)
    }
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(script_dir, 'models')
    
    # Create models directory if it doesn't exist
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        print(f"Created {models_dir} directory")
    
    # Saving the model
    model_path = os.path.join(models_dir, 'isolation_forest_anomaly_model.pkl')
    joblib.dump(model_data, model_path)
    print(f"Model saved to: {model_path}")
    
    
    # Test the model
    test_model(isolation_forest, scaler, feature_names)
    
    return isolation_forest, scaler, feature_names

def test_model(model, scaler, feature_names):
    """
    Test the trained model with sample data
    """
    print("\nTesting trained model with sample data:")
    
    # Normal sample
    normal_sample = {
        'heart_rate': 75,
        'systolic_bp': 120,
        'diastolic_bp': 80,
        'temperature': 36.8,
        'oxygen_level': 97,
        'respiratory_rate': 16,
        'glucose': 100,
        'room_temperature': 22,
        'humidity': 50,
        'air_quality': 25
    }
    
    # Prepare normal sample
    normal_features = np.array([[normal_sample.get(feature, 0) for feature in feature_names]])
    normal_scaled = scaler.transform(normal_features)
    normal_prediction = model.predict(normal_scaled)[0]
    normal_score = model.decision_function(normal_scaled)[0]
    
    print(f"Normal sample:")
    print(f"  - Prediction: {'Normal' if normal_prediction == 1 else 'Anomaly'}")
    print(f"  - Anomaly Score: {normal_score:.3f}")
    
    # Abnormal sample
    abnormal_sample = {
        'heart_rate': 140,  # High
        'systolic_bp': 180,  # High
        'diastolic_bp': 110,  # High
        'temperature': 39.5,  # High fever
        'oxygen_level': 85,  # Low
        'respiratory_rate': 35,  # High
        'glucose': 250,  # High
        'room_temperature': 30,  # High
        'humidity': 85,  # High
        'air_quality': 90  # Poor
    }
    
    # Prepare abnormal sample
    abnormal_features = np.array([[abnormal_sample.get(feature, 0) for feature in feature_names]])
    abnormal_scaled = scaler.transform(abnormal_features)
    abnormal_prediction = model.predict(abnormal_scaled)[0]
    abnormal_score = model.decision_function(abnormal_scaled)[0]
    
    print(f"Abnormal sample:")
    print(f"  - Prediction: {'Normal' if abnormal_prediction == 1 else 'Anomaly'}")
    print(f"  - Anomaly Score: {abnormal_score:.3f}")

def load_and_test_saved_model():
    """
    Load the saved model and test it
    """
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, 'models', 'isolation_forest_anomaly_model.pkl')
    
    try:
        print(f"\nLoading saved model from: {model_path}")
        model_data = joblib.load(model_path)
    except FileNotFoundError:
        print(f"Model file not found: {model_path}")
        return
    except Exception as e:
        print(f"Error loading model: {e}")
        return
    
    model = model_data['model']
    scaler = model_data['scaler']
    feature_names = model_data['feature_names']
    training_samples = model_data['training_samples']
    
    print(f"Model loaded successfully!")
    print(f"Training samples: {training_samples}")
    print(f"Features: {feature_names}")
    
    # Test the loaded model
    test_model(model, scaler, feature_names)

if __name__ == "__main__":
    # Train the model
    model, scaler, feature_names = train_isolation_forest_model()
    
    # Test loading the saved model
    load_and_test_saved_model()
