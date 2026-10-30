"""
Phase 4: Security Decision based on QBER
This file evaluates the measured QBER against a safety threshold.
"""

# In a realistic QKD scenario, a common theoretical threshold for BB84 
# is about 11% (or 0.11) before privacy amplification fails.
# For this prototype, we'll use 11% as our documented threshold.
QBER_THRESHOLD = 0.11

def evaluate_security(qber):
    """
    Evaluates whether the generated key is safe to use based on the QBER.
    Note: 11% is a documented prototype value for this project, not a universal limit for real QKD systems.
    """
    # Fix threshold-boundary display: if rounded equals threshold but real is above/below, show exact
    rounded_pct = round(qber * 100, 2)
    if rounded_pct == 11.00 and qber > 0.11:
        qber_str = f"{qber*100:.4f}%"
    else:
        qber_str = f"{qber*100:.2f}%"

    if qber <= QBER_THRESHOLD:
        status = "ACCEPTED"
        reason = f"QBER ({qber_str}) is below the 11% threshold."
    else:
        status = "REJECTED"
        reason = f"QBER ({qber_str}) exceeds the 11% threshold. Eve may be present."
        
    return status, reason

import os

_ml_model = None

def evaluate_security_ml(qber, num_qubits, sifted_len, adv_feat):
    """
    Evaluates whether the generated key is safe to use based on a Machine Learning model.
    """
    global _ml_model
    if _ml_model is None:
        import joblib
        model_path = os.path.join(os.path.dirname(__file__), 'models', 'qkd_model.pkl')
        if not os.path.exists(model_path):
            return "ERROR", "ML model not found. Please train it first.", 0.0
        _ml_model = joblib.load(model_path)
        
    sifted_ratio = sifted_len / num_qubits if num_qubits > 0 else 0
    
    import pandas as pd
    X = pd.DataFrame([{
        'qber': qber,
        'sifted_ratio': sifted_ratio,
        'qber_z': adv_feat['qber_z'],
        'qber_x': adv_feat['qber_x'],
        'qber_drift': adv_feat['qber_drift'],
        'max_burst': adv_feat['max_burst']
    }])
    
    prediction = _ml_model.predict(X)[0]
    probabilities = _ml_model.predict_proba(X)[0]
    attack_prob = probabilities[1]
    
    # prediction == 1 means Eve is present (Compromised)
    # prediction == 0 means Safe
    if prediction == 0:
        status = "ACCEPTED"
        confidence = probabilities[0] * 100
        reason = f"ML Classification: SAFE (Confidence: {confidence:.1f}%)."
    else:
        status = "REJECTED"
        confidence = probabilities[1] * 100
        reason = f"ML Classification: COMPROMISED (Confidence: {confidence:.1f}%). Eve detected!"
        
    return status, reason, attack_prob

if __name__ == '__main__':
    # Simple test cases
    print("Testing Security Decision:")
    print("Case 1: 0% QBER")
    print(evaluate_security(0.00))
    print("Case 2: 25% QBER (Typical full Eve attack)")
    print(evaluate_security(0.25))
