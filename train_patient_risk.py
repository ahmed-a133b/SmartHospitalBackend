import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
import os

# Loading and preprocessing the data
def load_and_preprocess_data():
   
    df = pd.read_csv(r'C:\Users\ahmed\OneDrive\Desktop\datasets\patient_risk_prediction.csv')
    
    
    df['conditions'] = df['conditions'].fillna('')
    
    # Features and target
    features = ['age', 'heart_rate', 'systolic_bp', 'diastolic_bp', 'temperature', 
                'oxygen_level', 'respiratory_rate', 'glucose', 'num_conditions', 'conditions']
    target = 'risk_level'
    
    X = df[features]
    y = df[target]
    
    # Encoding categorical variables
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', 'passthrough', ['age', 'heart_rate', 'systolic_bp', 'diastolic_bp', 
                                    'temperature', 'oxygen_level', 'respiratory_rate', 
                                    'glucose', 'num_conditions']),
            ('cat', OneHotEncoder(handle_unknown='ignore'), ['conditions'])
        ])
    
    return X, y, preprocessor


def train_model():
    X, y, preprocessor = load_and_preprocess_data()
    
    # Creating the pipeline
    model = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    
    # Splitting the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Training the model
    model.fit(X_train, y_train)
    
    # Evaluating the model
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    print(f"Training accuracy: {train_score:.4f}")
    print(f"Testing accuracy: {test_score:.4f}")
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(script_dir, 'models')
    
    # Create models directory if it doesn't exist
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        print(f"Created {models_dir} directory")
    
    # Saving the model
    model_path = os.path.join(models_dir, 'patient_risk_model.pkl')
    joblib.dump(model, model_path)
    print(f"Model saved to: {model_path}")
    
    return model

if __name__ == "__main__":
    model = train_model()