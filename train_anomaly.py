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

def generate_synthetic_training_data(num_samples=1000):
    """
    Generate synthetic training data for anomaly detection
    This creates realistic vital signs data with complete environmental data
    """
    training_data = []
    
    for i in range(num_samples):
        # Generate more realistic normal data with varied baselines for different patient types
        patient_type = random.choice(['young_healthy', 'middle_aged', 'elderly', 'pediatric'])
        
        if patient_type == 'young_healthy':
            base_hr, base_sys, base_dia = 68, 115, 75
            base_temp, base_o2, base_rr = 36.8, 99, 14
        elif patient_type == 'middle_aged':
            base_hr, base_sys, base_dia = 72, 125, 82
            base_temp, base_o2, base_rr = 37.0, 98, 16
        elif patient_type == 'elderly':
            base_hr, base_sys, base_dia = 75, 135, 85
            base_temp, base_o2, base_rr = 37.1, 97, 18
        else:  # pediatric
            base_hr, base_sys, base_dia = 85, 100, 65
            base_temp, base_o2, base_rr = 37.2, 99, 22
        
        data_point = {
            'heart_rate': np.random.normal(base_hr, 8),
            'systolic_bp': np.random.normal(base_sys, 12),
            'diastolic_bp': np.random.normal(base_dia, 8),
            'temperature': np.random.normal(base_temp, 0.3),
            'oxygen_level': np.random.normal(base_o2, 1.5),
            'respiratory_rate': np.random.normal(base_rr, 3),
            'glucose': np.random.normal(100, 15),  # Reduced variation for more realistic normal range
            # Environmental data with more realistic variation
            'env_temperature': np.random.normal(22, 1.5),  # Reduced variation
            'env_humidity': np.random.normal(45, 6),  # Reduced variation
            'env_air_quality': np.random.normal(85, 7),  # Reduced variation
            'env_noise_level': np.random.normal(35, 6),  # Reduced variation
            'env_co2_level': np.random.normal(400, 50),  # Reduced variation
            'env_light_level': np.random.normal(300, 40),  # Reduced variation
            'env_pressure': np.random.normal(1013.25, 2)  # Reduced variation
        }
        
        # Ensure values are within realistic bounds
        data_point['heart_rate'] = max(50, min(110, data_point['heart_rate']))
        data_point['systolic_bp'] = max(80, min(150, data_point['systolic_bp']))
        data_point['diastolic_bp'] = max(50, min(100, data_point['diastolic_bp']))
        data_point['temperature'] = max(35.5, min(38.0, data_point['temperature']))
        data_point['oxygen_level'] = max(90, min(100, data_point['oxygen_level']))
        data_point['respiratory_rate'] = max(10, min(25, data_point['respiratory_rate']))
        data_point['glucose'] = max(60, min(180, data_point['glucose']))
        # Environmental bounds - update field names to match API
        data_point['env_temperature'] = max(18, min(28, data_point['env_temperature']))
        data_point['env_humidity'] = max(25, min(80, data_point['env_humidity']))
        data_point['env_air_quality'] = max(40, min(100, data_point['env_air_quality']))
        data_point['env_noise_level'] = max(20, min(60, data_point['env_noise_level']))
        data_point['env_co2_level'] = max(300, min(800, data_point['env_co2_level']))
        data_point['env_light_level'] = max(150, min(500, data_point['env_light_level']))
        data_point['env_pressure'] = max(1000, min(1030, data_point['env_pressure']))
        
        training_data.append(data_point)
    
    return training_data

def generate_anomalous_training_data(num_samples=100):
    """
    Generate some anomalous training samples to improve model's detection capability
    This creates data points with various types of anomalies
    """
    anomalous_data = []
    
    for i in range(num_samples):
        # Start with normal baseline
        data_point = {
            'heart_rate': np.random.normal(75, 10),
            'systolic_bp': np.random.normal(120, 15),
            'diastolic_bp': np.random.normal(80, 10),
            'temperature': np.random.normal(36.8, 0.3),
            'oxygen_level': np.random.normal(97, 2),
            'respiratory_rate': np.random.normal(16, 3),
            'glucose': np.random.normal(100, 20),
            'env_temperature': np.random.normal(22, 2),
            'env_humidity': np.random.normal(45, 8),
            'env_air_quality': np.random.normal(85, 10),
            'env_noise_level': np.random.normal(35, 8),
            'env_co2_level': np.random.normal(400, 80),
            'env_light_level': np.random.normal(300, 60),
            'env_pressure': np.random.normal(1013.25, 3)
        }
        
        # Randomly introduce anomalies
        anomaly_type = random.choice(['vital_anomaly', 'environmental_anomaly', 'combined_anomaly'])
        
        if anomaly_type == 'vital_anomaly':
            # Introduce vital sign anomalies
            if random.random() < 0.5:  # Cardiac stress
                data_point['heart_rate'] = random.uniform(130, 180)
                data_point['systolic_bp'] = random.uniform(160, 200)
            else:  # Medical emergency
                data_point['temperature'] = random.uniform(39, 41)
                data_point['oxygen_level'] = random.uniform(75, 90)
                data_point['respiratory_rate'] = random.uniform(30, 45)
                
        elif anomaly_type == 'environmental_anomaly':
            # Introduce environmental anomalies
            data_point['env_temperature'] = random.uniform(32, 40)  # Too hot
            data_point['env_humidity'] = random.uniform(85, 95)  # Too humid
            data_point['env_air_quality'] = random.uniform(20, 40)  # Poor air
            data_point['env_noise_level'] = random.uniform(70, 90)  # Too noisy
            data_point['env_co2_level'] = random.uniform(800, 1500)  # High CO2
            data_point['env_light_level'] = random.uniform(10, 50)  # Too dim
            data_point['env_pressure'] = random.uniform(990, 1000)  # Low pressure
            
        else:  # combined_anomaly
            # Both vital and environmental issues
            data_point['heart_rate'] = random.uniform(110, 140)
            data_point['oxygen_level'] = random.uniform(88, 94)
            data_point['env_temperature'] = random.uniform(28, 35)
            data_point['env_co2_level'] = random.uniform(600, 1000)
            data_point['env_noise_level'] = random.uniform(60, 80)
        
        # Ensure bounds are still respected
        data_point['heart_rate'] = max(40, min(200, data_point['heart_rate']))
        data_point['systolic_bp'] = max(70, min(220, data_point['systolic_bp']))
        data_point['diastolic_bp'] = max(40, min(130, data_point['diastolic_bp']))
        data_point['temperature'] = max(32, min(42, data_point['temperature']))
        data_point['oxygen_level'] = max(70, min(100, data_point['oxygen_level']))
        data_point['respiratory_rate'] = max(8, min(50, data_point['respiratory_rate']))
        data_point['glucose'] = max(40, min(400, data_point['glucose']))
        data_point['env_temperature'] = max(10, min(45, data_point['env_temperature']))
        data_point['env_humidity'] = max(10, min(100, data_point['env_humidity']))
        data_point['env_air_quality'] = max(0, min(100, data_point['env_air_quality']))
        data_point['env_noise_level'] = max(15, min(100, data_point['env_noise_level']))
        data_point['env_co2_level'] = max(200, min(2000, data_point['env_co2_level']))
        data_point['env_light_level'] = max(5, min(1000, data_point['env_light_level']))
        data_point['env_pressure'] = max(980, min(1050, data_point['env_pressure']))
        
        anomalous_data.append(data_point)
    
    return anomalous_data

def prepare_features(data_list):
    """
    Convert list of data dictionaries to feature matrix
    """
    feature_names = ['heart_rate', 'systolic_bp', 'diastolic_bp', 'temperature', 
                    'oxygen_level', 'respiratory_rate', 'glucose', 'env_temperature', 
                    'env_humidity', 'env_air_quality', 'env_noise_level', 'env_co2_level', 
                    'env_light_level', 'env_pressure']
    
    features = []
    for data_point in data_list:
        row = [data_point.get(feature, 0) for feature in feature_names]
        features.append(row)
    
    return np.array(features), feature_names

def train_isolation_forest_model():
    """
    Train Isolation Forest model with complete environmental data and save to models folder
    """
    print("Starting Isolation Forest model training with complete environmental data...")
    
    # Generate normal training data
    normal_training_data = generate_synthetic_training_data(1500) 
    print(f"Generated {len(normal_training_data)} normal synthetic data points")
    
    # Generate some anomalous data for better model understanding
    anomalous_training_data = generate_anomalous_training_data(250)
    print(f"Generated {len(anomalous_training_data)} anomalous synthetic data points")
    
    # Combine all training data
    all_training_data = normal_training_data + anomalous_training_data
    print(f"Total training samples: {len(all_training_data)}")
    
    # Prepare features
    X_train, feature_names = prepare_features(all_training_data)
    print(f"Feature matrix shape: {X_train.shape}")
    print(f"Features: {feature_names}")
    print("Environmental features included:")
    env_features = [f for f in feature_names if f in ['env_temperature', 'env_humidity', 'env_air_quality', 'env_noise_level', 'env_co2_level', 'env_light_level', 'env_pressure']]
    for i, feature in enumerate(env_features, 1):
        print(f"  {i}. {feature}")
    
    # Initialize and fit scaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)
    print("Data normalized using StandardScaler")
    
    # Initialize and train Isolation Forest with more restrictive contamination
    # Reduce contamination rate to make model less sensitive to normal variations
    contamination_rate = min(0.05, len(anomalous_training_data) / len(all_training_data))  # Cap at 5%
    print(f"Using contamination rate: {contamination_rate:.3f} (reduced for better precision)")
    
    isolation_forest = IsolationForest(
        contamination=contamination_rate,  # More restrictive contamination
        random_state=42,
        n_estimators=200,  # Increased for better performance
        max_samples=0.8,  # Use subset of samples for each tree
        max_features=0.8,  # Use subset of features for each tree  
        bootstrap=True  # Enable bootstrapping for variety
    )
    
    print("Training Isolation Forest with enhanced environmental features...")
    isolation_forest.fit(X_scaled)
    print("Training completed!")
    
    # Print feature importance information
    print("\nFeature statistics from training data:")
    for i, feature in enumerate(feature_names):
        feature_data = X_train[:, i]
        print(f"  {feature}: mean={feature_data.mean():.2f}, std={feature_data.std():.2f}, "
              f"range=[{feature_data.min():.2f}, {feature_data.max():.2f}]")
    
    # Save model and scaler
    model_data = {
        'model': isolation_forest,
        'scaler': scaler,
        'feature_names': feature_names,
        'training_samples': len(all_training_data),
        'normal_samples': len(normal_training_data),
        'anomalous_samples': len(anomalous_training_data),
        'contamination_rate': contamination_rate
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
    
    # Normal sample with complete environmental data
    normal_sample = {
        'heart_rate': 75,
        'systolic_bp': 120,
        'diastolic_bp': 80,
        'temperature': 36.8,
        'oxygen_level': 97,
        'respiratory_rate': 16,
        'glucose': 100,
        'env_temperature': 22,
        'env_humidity': 45,
        'env_air_quality': 85,
        'env_noise_level': 35,
        'env_co2_level': 400,
        'env_light_level': 300,
        'env_pressure': 1013.25
    }
    
    # Prepare normal sample
    normal_features = np.array([[normal_sample.get(feature, 0) for feature in feature_names]])
    normal_scaled = scaler.transform(normal_features)
    normal_prediction = model.predict(normal_scaled)[0]
    normal_score = model.decision_function(normal_scaled)[0]
    
    print(f"Normal sample:")
    print(f"  - Prediction: {'Normal' if normal_prediction == 1 else 'Anomaly'}")
    print(f"  - Anomaly Score: {normal_score:.3f}")
    
    # Abnormal sample with environmental anomalies
    abnormal_sample = {
        'heart_rate': 140,  # High
        'systolic_bp': 180,  # High
        'diastolic_bp': 110,  # High
        'temperature': 39.5,  # High fever
        'oxygen_level': 85,  # Low
        'respiratory_rate': 35,  # High
        'glucose': 250,  # High
        'env_temperature': 30,  # High
        'env_humidity': 85,  # High
        'env_air_quality': 40,  # Poor (low is bad for air quality)
        'env_noise_level': 75,  # Very loud
        'env_co2_level': 1000,  # High CO2
        'env_light_level': 50,  # Very dim
        'env_pressure': 995  # Low atmospheric pressure
    }
    
    # Prepare abnormal sample
    abnormal_features = np.array([[abnormal_sample.get(feature, 0) for feature in feature_names]])
    abnormal_scaled = scaler.transform(abnormal_features)
    abnormal_prediction = model.predict(abnormal_scaled)[0]
    abnormal_score = model.decision_function(abnormal_scaled)[0]
    
    print(f"Abnormal sample:")
    print(f"  - Prediction: {'Normal' if abnormal_prediction == 1 else 'Anomaly'}")
    print(f"  - Anomaly Score: {abnormal_score:.3f}")
    
    # Environmental-only anomaly sample (normal vitals, bad environment)
    env_anomaly_sample = {
        'heart_rate': 72,  # Normal
        'systolic_bp': 118,  # Normal
        'diastolic_bp': 78,  # Normal
        'temperature': 36.9,  # Normal
        'oxygen_level': 98,  # Normal
        'respiratory_rate': 15,  # Normal
        'glucose': 95,  # Normal
        'env_temperature': 35,  # Very hot
        'env_humidity': 95,  # Very humid
        'env_air_quality': 30,  # Poor air quality
        'env_noise_level': 80,  # Very noisy
        'env_co2_level': 1200,  # Dangerous CO2 levels
        'env_light_level': 20,  # Almost dark
        'env_pressure': 980  # Very low pressure
    }
    
    # Prepare environmental anomaly sample
    env_features = np.array([[env_anomaly_sample.get(feature, 0) for feature in feature_names]])
    env_scaled = scaler.transform(env_features)
    env_prediction = model.predict(env_scaled)[0]
    env_score = model.decision_function(env_scaled)[0]
    
    print(f"Environmental anomaly sample (normal vitals, bad environment):")
    print(f"  - Prediction: {'Normal' if env_prediction == 1 else 'Anomaly'}")
    print(f"  - Anomaly Score: {env_score:.3f}")

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
    normal_samples = model_data.get('normal_samples', 'unknown')
    anomalous_samples = model_data.get('anomalous_samples', 'unknown')
    contamination_rate = model_data.get('contamination_rate', 'unknown')
    
    print(f"Model loaded successfully!")
    print(f"Total training samples: {training_samples}")
    print(f"Normal samples: {normal_samples}")
    print(f"Anomalous samples: {anomalous_samples}")
    print(f"Contamination rate: {contamination_rate}")
    print(f"Features ({len(feature_names)}): {feature_names}")
    
    # Verify all environmental features are included
    env_features = [f for f in feature_names if f in ['env_temperature', 'env_humidity', 'env_air_quality', 'env_noise_level', 'env_co2_level', 'env_light_level', 'env_pressure']]
    print(f"Environmental features ({len(env_features)}): {env_features}")
    
    # Test the loaded model
    test_model(model, scaler, feature_names)

if __name__ == "__main__":
    # Train the model
    model, scaler, feature_names = train_isolation_forest_model()
    
    # Test loading the saved model
    load_and_test_saved_model()
