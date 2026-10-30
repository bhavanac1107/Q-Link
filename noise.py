from qiskit_aer.noise import NoiseModel, depolarizing_error

def get_depolarizing_noise_model(error_rate):
    """
    Creates a Qiskit noise model with a depolarizing error.
    
    The 'error_rate' (p) is the target bit-flip probability.
    Qiskit's depolarizing_error(lam, 1) flips a measured bit with probability lam/2,
    so we use lam = min(2 * p, 1.0) internally to match the target error rate.
    
    Args:
        error_rate (float): The target probability of a bit flip (0.0 to 0.5).
        
    Returns:
        NoiseModel: The constructed noise model, or None if error_rate is 0.
    """
    if error_rate <= 0.0:
        return None
        
    # Validate error rate
    error_rate = max(0.0, min(error_rate, 0.5))
    
    noise_model = NoiseModel()
    
    # Calculate lambda for Qiskit
    lam = min(2.0 * error_rate, 1.0)
    error_1q = depolarizing_error(lam, 1)
    
    # Apply ONLY to 'id' gates representing the transmission channel.
    # This ensures QBER is roughly p regardless of how many other gates exist.
    noise_model.add_all_qubit_quantum_error(error_1q, ['id'])
    
    return noise_model
