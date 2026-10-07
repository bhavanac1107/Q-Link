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
    if qber <= QBER_THRESHOLD:
        status = "ACCEPTED"
        reason = f"QBER ({qber*100:.1f}%) is below the prototype threshold of 11%."
    else:
        status = "REJECTED"
        reason = f"QBER ({qber*100:.1f}%) exceeds the prototype threshold of 11%. Eve may be present."
        
    return status, reason

if __name__ == '__main__':
    # Simple test cases
    print("Testing Security Decision:")
    print("Case 1: 0% QBER")
    print(evaluate_security(0.00))
    print("Case 2: 25% QBER (Typical full Eve attack)")
    print(evaluate_security(0.25))
