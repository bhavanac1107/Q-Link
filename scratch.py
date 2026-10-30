from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import time

n = 2000
qc = QuantumCircuit(n, 2*n)
qc.x(range(n//2))
qc.h(range(n))
# bob measures
qc.measure(range(n), range(n, 2*n))

start = time.time()
sim = AerSimulator(method='stabilizer')
comp = transpile(qc, sim, optimization_level=0)
res = sim.run(comp, shots=1).result()
end = time.time()
print(f"Time: {end-start:.3f}s")
