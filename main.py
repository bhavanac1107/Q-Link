"""
Phase 1: Basic Quantum Circuit
This file demonstrates a basic 1-qubit quantum circuit using Qiskit.
It applies a Hadamard gate, measures the qubit, and runs a simulation.
"""

import qiskit
import qiskit_aer
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

def run_basic_circuit():
    """
    Creates a 1-qubit circuit with a Hadamard gate, measures it,
    and runs it 1024 times on the Qiskit Aer simulator.
    """
    print(f"Qiskit version: {qiskit.__version__}")
    print(f"Qiskit Aer version: {qiskit_aer.__version__}")
    print("-" * 50)
    
    # 1. Create a Quantum Circuit acting on a quantum register of one qubit
    # We specify 1 qubit and 1 classical bit (to store the measurement)
    circuit = QuantumCircuit(1, 1)
    
    # 2. Add a Hadamard (H) gate on qubit 0.
    # Important Quantum Concept: A Hadamard gate takes a qubit initially in state |0>
    # and puts it into an equal superposition. This means the qubit is in a state
    # where it has a 50% probability of being measured as 0 and a 50% probability of being 1.
    circuit.h(0)
    
    # 3. Map the quantum measurement to the classical bit
    circuit.measure(0, 0)
    
    print("Circuit Diagram:")
    print(circuit.draw())
    print("-" * 50)
    
    # 4. Use AerSimulator for the simulation
    # We use AerSimulator() per the modern API guidelines.
    simulator = AerSimulator()
    
    # 5. Transpile the circuit for the simulator
    # Transpilation optimizes the circuit for the specific target backend.
    compiled_circuit = transpile(circuit, simulator)
    
    # 6. Run the compiled circuit and get the result counts
    # We use 1024 shots (executions) to get a statistically significant distribution.
    result = simulator.run(compiled_circuit, shots=1024).result()
    counts = result.get_counts(circuit)
    
    print(f"Measurement counts for 1024 shots: {counts}")
    print("-" * 50)
    
    # 7. Explanation
    print("Output Explanation:")
    print("A Hadamard gate puts a qubit into an equal superposition of 0 and 1.")
    print("When we measure it, quantum mechanics dictates a 50% probability of measuring '0'")
    print("and a 50% probability of measuring '1'.")
    print("Because the simulation uses 1024 shots (measurements), we expect roughly 512 zeros and 512 ones.")
    print("The exact numbers differ slightly each run due to the inherent randomness of quantum measurements")
    print("(or in this case, pseudo-randomness of the simulator).")

if __name__ == '__main__':
    run_basic_circuit()
