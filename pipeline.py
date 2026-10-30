import numpy as np

def simple_error_correction(alice_key, bob_key, block_size=8):
    """
    A simplified single-pass Cascade-like error correction.
    Uses binary search to find and correct 1 error per mismatched block.
    """
    corrected_alice = []
    corrected_bob = []
    
    def fix_error(a_blk, b_blk):
        if len(a_blk) == 1:
            return a_blk, a_blk # Correct Bob's bit to match Alice's bit
        mid = len(a_blk) // 2
        if sum(a_blk[:mid]) % 2 != sum(b_blk[:mid]) % 2:
            left_a, left_b = fix_error(a_blk[:mid], b_blk[:mid])
            return left_a + a_blk[mid:], left_b + b_blk[mid:]
        else:
            right_a, right_b = fix_error(a_blk[mid:], b_blk[mid:])
            return a_blk[:mid] + right_a, b_blk[:mid] + right_b

    for i in range(0, len(alice_key), block_size):
        a_block = list(alice_key[i:i+block_size])
        b_block = list(bob_key[i:i+block_size])
        
        if len(a_block) < block_size:
            break
            
        a_parity = sum(a_block) % 2
        b_parity = sum(b_block) % 2
        
        if a_parity != b_parity:
            a_block, b_block = fix_error(a_block, b_block)
            
        corrected_alice.extend(a_block[1:])
        corrected_bob.extend(b_block[1:])
            
    return np.array(corrected_alice, dtype=np.int8), np.array(corrected_bob, dtype=np.int8)

def privacy_amplification(key, original_qber):
    """
    Applies universal hashing to compress the key and eliminate Eve's partial information.
    The amount of compression depends on the estimated QBER.
    """
    n = len(key)
    if n == 0:
        return np.array([])
        
    def binary_entropy(p):
        if p <= 0.0 or p >= 1.0: return 0.0
        return -p * np.log2(p) - (1 - p) * np.log2(1 - p)
        
    # Fraction of information Eve might know (based on theoretical bounds)
    # We compress the key by this fraction.
    leakage_fraction = binary_entropy(original_qber)
    
    final_len = int(n * (1.0 - leakage_fraction))
    
    if final_len <= 0:
        return np.array([])
        
    # We use a simple Toeplitz matrix multiplication (modulo 2) as a universal hash function
    # For speed and simplicity in the prototype, we simulate this by taking a random slice 
    # of the required length (in a real system, the seed for the matrix is public).
    
    # Generate a random Toeplitz matrix
    np.random.seed(42) # Fixed seed for reproducibility between Alice and Bob
    matrix = np.random.randint(2, size=(final_len, n))
    
    final_key = np.dot(matrix, key) % 2
    return final_key.astype(np.int8)
