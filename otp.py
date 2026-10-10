def encrypt_message(message, key):
    """
    Encrypts a string message using a binary key (One-Time Pad).
    Converts message to binary, XORs with the key, and returns the binary ciphertext.
    """
    if len(key) == 0:
        return ""
        
    # Convert message to binary string using UTF-8
    msg_bytes = message.encode('utf-8')
    binary_message = ''.join(format(b, '08b') for b in msg_bytes)
    
    if len(binary_message) > len(key):
        return f"ERROR: Message requires {len(binary_message)} bits, but key is only {len(key)} bits long. Cannot reuse key."
        
    # XOR with key
    ciphertext = []
    for i in range(len(binary_message)):
        bit = int(binary_message[i])
        key_bit = int(key[i])
        ciphertext.append(str(bit ^ key_bit))
        
    return ''.join(ciphertext)

def decrypt_message(ciphertext, key):
    """
    Decrypts a binary ciphertext using the binary key.
    """
    if ciphertext.startswith("ERROR") or len(ciphertext) == 0:
        return ""
        
    # XOR with key
    plaintext_binary = []
    for i in range(len(ciphertext)):
        bit = int(ciphertext[i])
        key_bit = int(key[i])
        plaintext_binary.append(str(bit ^ key_bit))
        
    binary_str = ''.join(plaintext_binary)
    
    # Convert back to string using UTF-8
    byte_array = bytearray()
    for i in range(0, len(binary_str), 8):
        byte = binary_str[i:i+8]
        if len(byte) == 8:
            byte_array.append(int(byte, 2))
            
    try:
        plaintext = byte_array.decode('utf-8')
    except UnicodeDecodeError:
        plaintext = byte_array.decode('utf-8', errors='replace')
        
    return plaintext
