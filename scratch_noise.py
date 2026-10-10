from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

n = 100
qc = QuantumCircuit(n, n)
qc.h(range(n))
qc.measure(range(n), range(n))

noise_model = NoiseModel()
error = depolarizing_error(0.1, 1)
# Apply noise to all single qubit gates
noise_model.add_all_qubit_quantum_error(error, ['h', 'x', 'id'])

sim = AerSimulator(method='stabilizer', noise_model=noise_model)
comp = transpile(qc, sim)
result = sim.run(comp, shots=1).result()
counts = result.get_counts()
print(counts)
