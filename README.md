# Q-Link: Quantum-Secure Communication Using the BB84 Protocol

**Detect. Protect. Secure.**

Q-Link is an interactive quantum key distribution (QKD) simulator built using Python, Streamlit, and Qiskit Aer. It demonstrates how Alice and Bob can establish a shared secret key using the BB84 protocol, detect potential eavesdropping by Eve, and use the generated key to encrypt and decrypt messages.

The project combines quantum circuit simulation, security monitoring, data visualization, and machine learning diagnostics to make quantum communication security easier to understand.

*Note: Q-Link is an educational simulator. It does not use real photons or quantum hardware and is not a production-ready security system.*

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Objectives](#objectives)
- [Key Features](#key-features)
- [How It Works](#how-it-works)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Simulation Results](#simulation-results)
- [Getting Started](#getting-started)
- [How to Use](#how-to-use)
- [Machine Learning Evaluation](#machine-learning-evaluation)
- [Assumptions and Limitations](#assumptions-and-limitations)
- [Future Enhancements](#future-enhancements)
- [References](#references)
- [Team](#team)

## Overview

Traditional cryptographic systems such as RSA and ECC rely on mathematical problems that could be vulnerable to sufficiently powerful quantum computers. 

Quantum Key Distribution offers a different approach to key establishment. The BB84 protocol uses quantum states and measurements in different bases to help detect potential eavesdropping. 

Q-Link simulates this process and visualizes how channel noise and an intercept-resend attack affect the Quantum Bit Error Rate (QBER). The simulator also demonstrates how the resulting secret key can be used for message encryption with a one-time pad.

## Problem Statement

How can two parties establish a shared secret key while detecting potential eavesdropping during communication? 

Q-Link addresses this problem by simulating BB84 quantum key distribution, estimating the error rate, applying a key-acceptance rule, and alerting the operator when a session fails the configured security checks.

## Objectives

- Simulate the BB84 quantum key distribution protocol.
- Demonstrate eavesdropping through an intercept-resend attack.
- Estimate QBER to identify suspicious communication sessions.
- Apply error correction and key confirmation.
- Demonstrate message encryption and decryption using a one-time pad.
- Monitor repeated communication sessions through a security dashboard.
- Evaluate machine learning as a supplementary attack-detection aid.

## Key Features

1. **BB84 Simulation**
Configure the number of qubits, channel noise, Eve's interception percentage, attack type, and key-acceptance method.
2. **Results and Analysis**
Visualize sifted key length, QBER, error-corrected key length, final secret key, key rate, quantum circuits, and per-qubit results.
3. **Live Encryption Demo**
Encrypt a message using a one-time pad, inspect the ciphertext, and observe Bob decrypting the message with the shared key.
4. **Link Monitor**
Monitor multiple communication sessions, introduce Eve at a selected session, track alerts and rejected transfers, and export a JSON report.
5. **Machine Learning Diagnostics**
Use a Random Forest classifier to analyze simulated communication sessions and estimate the likelihood of an attack.
6. **Multiple Perspectives**
Explore the same communication run from Alice's, Bob's, Eve's, and the operator's perspectives.

## How It Works

The BB84 workflow consists of the following stages:

- **State Preparation**: Alice generates random bits and randomly selects rectilinear (+) or diagonal (×) bases.
- **Quantum Transmission**: Alice sends the encoded qubits through a simulated quantum channel.
- **Measurement**: Bob measures the received qubits using randomly selected bases.
- **Key Sifting**: Alice and Bob compare their bases publicly and retain positions where their bases match.
- **QBER Estimation**: They compare a random sample of the sifted bits to estimate the error rate.
- **Error Correction**: A Cascade-style reconciliation process corrects key mismatches.
- **Key Confirmation**: SHA-256 hashes are compared to check whether both parties hold matching keys.
- **Privacy Amplification**: The reconciled key is compressed to reduce information potentially available to an eavesdropper.
- **Security Decision**: The session is rejected if QBER exceeds the configured 11% threshold or key confirmation fails.
- **Message Encryption**: The accepted key is used in the one-time-pad demonstration.

### Understanding QBER
QBER stands for Quantum Bit Error Rate. It measures the proportion of compared bits that differ between Alice and Bob.
- **Approximately 0%**: Expected in an ideal, noiseless simulation without Eve.
- **Approximately 1–8%**: Possible in the project's noise-only simulation scenarios.
- **Approximately 25%**: Expected on average for a full intercept-resend attack with randomly selected BB84 bases under idealized assumptions.

*These are theoretical expectations or observed simulation ranges, not guaranteed values for every run.*

## System Architecture

```text
               EVE (Optional)
                     |
                     v
ALICE ------> Quantum Channel ------> BOB
        |     (Qubits + Noise)        |
        |                             |
        +-------- Classical Channel --+
(Basis Comparison, QBER, Key Confirmation)
                     |
                     v
             SECURITY MONITOR
         QBER Analysis and Alerts
                     |
                     v
             FINAL SECRET KEY
                     |
                     v
             ONE-TIME-PAD DEMO
```

## Technology Stack

| Technology | Purpose |
| --- | --- |
| **Python** | Core application logic |
| **Streamlit** | Interactive web interface |
| **Qiskit Aer** | Quantum circuit simulation |
| **Plotly** | Charts and data visualization |
| **scikit-learn** | Random Forest diagnostics |
| **SHA-256** | Key confirmation |
| **Git and GitHub** | Version control and project hosting |

## Simulation Results

### Clean Communication Scenario
Example run with Eve disabled and channel noise set to zero:

| Metric | Result |
| --- | --- |
| Qubits sent | 1,846 |
| Sifted key | 911 bits |
| Estimated QBER | 0.00% |
| QBER sample | 227 bits |
| Key after Cascade | 595 bits |
| Final secret key | 595 bits |
| Key rate | 0.32 bits per qubit |
| ML diagnostic | Safe; 0.5% estimated attack probability |

### Eavesdropping Scenario
Example Link Monitor run with 20 sessions and Eve intercepting 100% of qubits from session 8:

| Metric | Result |
| --- | --- |
| Total sessions | 20 |
| Transfers delivered | 7 |
| Transfers blocked | 13 |
| Detection delay | 0 sessions |
| False alarms before Eve | 0 |
| QBER during attack | Approximately 20–30% |
| QBER threshold | 11% |

*These results are examples from a particular simulation configuration. Different random seeds and settings may produce different values.*

## Getting Started

### Prerequisites
- Python 3.10 or newer
- pip
- Git
- A code editor such as Visual Studio Code

### 1. Clone the Repository
```bash
git clone <YOUR-GITHUB-REPOSITORY-URL>
cd <YOUR-PROJECT-FOLDER>
```
*(Replace the placeholders with your actual GitHub repository URL and project folder name.)*

### 2. Create a Virtual Environment

**Windows PowerShell:**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux or macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the Application
If your Streamlit entry point is `app.py`, execute:
```bash
streamlit run app.py
```
*(If your main application file has a different name, replace app.py with that filename.)*

The application should open in your browser at: `http://localhost:8501`

## How to Use

1. Open the **Home / Simulation** page.
2. Set Eve's interception to 0% and channel noise to 0% for a clean baseline.
3. Run the simulation and examine the results.
4. Open **Results & Analysis** to inspect QBER, key lengths, and diagnostic charts.
5. Open **Live Encryption Demo** to encrypt and decrypt a message.
6. Open **Link Monitor** and configure 20 sessions with Eve starting at session 8.
7. Observe how the QBER threshold affects session acceptance and rejection.
8. Try a lower interception percentage to investigate how weaker attacks affect detection.
9. Export the session report for further analysis.

## Machine Learning Evaluation

The project compares a fixed QBER threshold with a Random Forest diagnostic using 7,600 simulated sessions.
The classifier uses features including:
- Z-basis QBER
- X-basis QBER
- QBER drift
- Maximum burst error

The current implementation uses the 11% QBER threshold for the security decision. The ML model provides supplementary diagnostics rather than independently accepting or rejecting keys.

Offline evaluation revealed that the model can produce excessive false alarms or miss attacks when the attack type changes. This highlights the importance of testing machine learning models on unseen attack scenarios and different channel conditions.

*Important: The evaluation uses simulated data from the same simulator, not real quantum hardware measurements.*

## Assumptions and Limitations

- The application is a simulation and does not transmit real quantum states.
- The classical communication channel is assumed to be authenticated; authentication is not implemented in the current version.
- Channel noise is represented by a simplified noise setting.
- Only Standard Random and Biased Eve attack types are currently supported.
- The 11% threshold is a simplified decision rule based on an asymptotic BB84 security result; it is not a complete security proof for this implementation.
- Finite-key security analysis is not implemented.
- The machine learning model has not been validated on real quantum hardware data.
- The one-time-pad demonstration requires a key at least as long as the message, and a secure one-time pad must never reuse its key.
- Q-Link is an educational and research prototype, not a production messaging or security product.

## Future Enhancements

- Improve dashboard layout, chart labels, and mobile responsiveness.
- Add automated tests and GitHub Actions continuous integration.
- Add more Eve attack models and realistic channel noise models.
- Implement adaptive QBER thresholds and finite-key analysis.
- Improve error reconciliation and privacy amplification.
- Add authenticated classical communication.
- Evaluate machine learning on unseen attack types and noise conditions.
- Add explainable ML diagnostics and anomaly detection.
- Compare classical and quantum key establishment visually.
- Support multiple interconnected quantum communication links.
- Add optional experiments on real quantum cloud hardware.
- Explore additional protocols such as B92, E91, and six-state QKD.

## References

1. Bennett, C. H., and Brassard, G. (1984). Quantum cryptography: Public key distribution and coin tossing.
2. Shor, P. W. (1997). Polynomial-time algorithms for prime factorization and discrete logarithms on a quantum computer. *SIAM Journal on Computing*.
3. Wootters, W. K., and Zurek, W. H. (1982). A single quantum cannot be cloned. *Nature*.
4. Shor, P. W., and Preskill, J. (2000). Simple proof of security of the BB84 quantum key distribution protocol. *Physical Review Letters*.
5. Brassard, G., and Salvail, L. (1993). Secret-key reconciliation by public discussion.
6. Bennett, C. H., Brassard, G., and Robert, J.-M. (1988). Privacy amplification by public discussion.
7. Scarani, V., et al. (2009). The security of practical quantum key distribution. *Reviews of Modern Physics*.

## Team

- **Project:** Q-Link
- **Team Name:** Add your team name
- **Team Lead:** Add your team lead's name
- **Event:** Q-Hack India 2026
- **Track:** Open Quantum Innovation

## License

Add your chosen open-source license here. If you choose MIT, include an `MIT LICENSE` file in the repository.

---

**Q-Link — Detect. Protect. Secure.**

Exploring quantum communication security through interactive simulation.
