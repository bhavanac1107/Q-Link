import os
import sys
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

def train_and_save_model():
    print("Loading dataset...")
    try:
        df = pd.read_csv("results/ml_dataset.csv")
    except FileNotFoundError:
        print("Error: Dataset not found. Please run experiments/generate_ml_data.py first.")
        sys.exit(1)
        
    # Features: QBER and sifted length (as a fraction of num_qubits)
    # We can use qber and sifted_len/num_qubits
    df['sifted_ratio'] = df['sifted_len'] / df['num_qubits']
    
    # We use qber, num_qubits, and sifted_ratio as features
    X = df[['qber', 'num_qubits', 'sifted_ratio']]
    y = df['eve_present']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"Training Random Forest on {len(X_train)} samples...")
    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X_train, y_train)
    
    print("Evaluating model...")
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    
    print(f"\nAccuracy: {acc * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Safe (Eve OFF)", "Compromised (Eve ON)"]))
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    os.makedirs('models', exist_ok=True)
    model_path = 'models/qkd_model.pkl'
    joblib.dump(model, model_path)
    print(f"\nModel saved successfully to {model_path}")

if __name__ == "__main__":
    train_and_save_model()
