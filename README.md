# Q-Link: Quantum Key Distribution with Attack Detection

This is a prototype of Q-LINK, built for Q-Hack India 2026.

## Problem
Secure communication is critical, but classical encryption methods like RSA rely on computational hardness, which could be broken by future quantum computers (e.g., using Shor's algorithm). 

## Why Quantum Computing is Relevant
Quantum Key Distribution (QKD) leverages the fundamental principles of quantum mechanics (like superposition and the observer effect) to establish a shared secret key. Eavesdropping introduces detectable errors because observing a quantum state inevitably alters it.

## Phases
Currently, we have implemented the First Prototype Scope:
- **Phase 1:** Basic quantum circuit to demonstrate superposition.
- **Phase 2:** BB84 simulation (Alice encrypts, Bob measures and sifts).
- **Phase 3:** Eve attack (Intercept-resend and QBER sampling).
- **Phase 4:** Security decision based on QBER threshold.

*Planned next steps:*
- Phase 5: Noise simulation
- Phase 6: Machine Learning classification of noise vs. attack
- Phase 7: Simple message encryption/decryption
- Phase 8: Expanded interactive Streamlit dashboard
- Phase 9: Optional E91/CHSH module
- Phase 10: Optional IBM Quantum hardware execution

## Installation
```bash
# In the Qlinks directory
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## How to run
```bash
# To run the Phase 1 basic quantum circuit:
python main.py

# To run the Phase 2 BB84 script:
python bb84.py

# To run the Phase 3 Eve script:
python eve.py

# To run the Streamlit Dashboard (Prototype):
streamlit run app.py
```

## How to run tests
```bash
python tests/test_sanity.py
```
