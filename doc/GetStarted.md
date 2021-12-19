SpinQKit is the quantum software development kit from SpinQ Technology Co., Ltd. This is a simple manual on how to use SpinQKit. Later we will provide a comprehensive tutorial with more explanations and examples. 

## 1 Get Started

### 1.1 Install
SpinQKit can be installed using the following command:

``pip install spinqkit``

The package requires Python 3.8+. We have tested the package on Ubuntu 20.04 and Windows 10 with Python 3.8 and 3.9.

### 1.2 Development

There are three basic steps to write and run a quantum program using SpinQKit. First, write code using one of the three syntaxes supported in SpinQKit: our own native Python syntax which will be introduced below, OpenQASM 2.0 syntax, and IBM Qiskit Python syntax. Second, compile the code to an intermediate representation using the corresponding compiler. Third, choose a backend, execute the intermediate representation, and get the result. SpinQKit has three different backends: the SpinQ classical simulator, the SpinQ cloud, and the Triangulum quantum computer from SpinQ.

The following example is a simple quantum program using our SpinQKit Python syntax. 

```
from spinqkit import get_basic_simulator, get_compiler, Circuit, BasicSimulatorConfig
from spinqkit import H, CX, Rx
from math import pi

comp = get_compiler("native")
engine = get_basic_simulator()

circ = Circuit()
q = circ.allocateQubits(2)
circ << (Rx, q[0], pi)
circ << (H, q[1])
circ << (CX, (q[0], q[1]))

optimization_level = 0
exe = comp.compile(circ, optimization_level)
config = BasicSimulatorConfig()
config.configure_shots(1024)

result = engine.execute(exe, config)
print(result.counts)
```

In this example, the get_compiler method is used to choose the compiler. The three options are “native”, “qasm”, and “qiskit”. All the compilers have a compile method with two arguments, and the second argument is always the optimization level, but the first argument is different. The native compiler takes a Circuit instance in SpinQKit as the first argument. The qasm compiler takes the path to a qasm file as the first argument. The qiskit compiler takes a Qiskit QuantumCircuit instance as the first argument.

The get_basic_simulator method is used to choose the SpinQ classical simulator. Similarly, get_spinq_cloud and get_triangulum are for the SpinQ cloud and our Triangulum quantum computer respectively.

### 1.3 Backend

In the example above, the total number of shots is configured for the SpinQ simulator so that the count of each possible binary reading is calculated in the result. You can also choose the qubits to measure using the configure_measure_qubits method of BasicSimulatorConfig. This configuration is only available for the SpinQ simulator. By default, all the qubits will be measured.   

For the Triangulum computer (in TriangulumConfig), the IP address of Triangulum must be configured. You can also configure the task name and description. Please refer to the manual of Triangulum for more details.

In order to use the SpinQ cloud, you have to first register and add a public SSH key on [https://cloud.spinq.cn](https://cloud.spinq.cn). Please refer to the documentation online about the SpinQ cloud [https://cloud.spinq.cn/#/docs](https://cloud.spinq.cn/#/docs). Username and key information are required in the get_spinq_cloud method. We provide multiple platforms with different number of qubits on the SpinQ cloud. The cloud backend has a get_platform method, and this method can provide four platforms “gemini_vp”, “nmr_vp_4”, “nmr_vp_6”, “superconductor_vp”. These platforms have 2, 4, 6, and 8 qubits respectively and support only quantum programs with fewer qubits. There is an example about how to use the cloud service in *spinqkit/example/cloud_example.py*.

### 1.4 Result

SpinQKit provides four types of results. First, all the backends can provide the probabilities of binary readings. Please notice that SpinQKit uses the little endian, i.e., the first bit in the result binary string corresponds to the first qubit in the quantum circuit. Instead IBM Qiskit uses the big endian. In order to compare the results from SpinQKit and Qiskit, you need to reverse the Qiskit binary string. Second,  the count of each possible binary reading can be found in the result only when the simulator backend is used. The total number of shots is configured otherwise 1024 will be used by default. Third, with the simulator, the result also has a list of possible binary readings. The number of a binary string in the list is also the count of the string in the result of counts. Fourth, the simulator backend can provide a state vector of all the qubits when there is no measure gate or conditional gate based on the value of a classical register.

## 2 Programming Language

### 2.1 SpinQKit Python Syntax

**Circuit**: In SpinQKit, each quantum program is a Circuit instance.

**Quantum register and classical register**: A quantum register has a certain number of qubits, and must be allocated by a circuit. A qubit is represented by the register name and the index. A classical register has a certain number of classical bits, and must be allocated by a circuit. A bit is  represented by the register name and the index.
 
**Quantum gates**: SpinQKit defines 20 logic quantum gates (I, H, X, Y, Z, Rx, Ry, Rz, P, T, Td, S, Sd, CX/CNOT, CY, CZ, U, CP, SWAP, CCX) and two special gates (MEASURE and BARRIER).

**Instruction**: An instruction consists of a quantum gate, qubits, optional classical bits, and optional rotation radian for rotation gates. SpinQKit uses << to add an instruction to a circuit, as shown in the example above.

**Custom quantum gate**: SpinQKit provides a gate builder to define a custom quantum gate. The builder builds a gate based on sub-gates. There are qubit indexes and optional parameter lambda for each sub-gate. For example, the SWAP builder can use three CX gates, as follows:

```
SWAP_builder = GateBuilder(2)
SWAP_builder.append(CX, [0, 1])
SWAP_builder.append(CX, [1, 0])
SWAP_builder.append(CX, [0, 1])
SWAP = SWAP_builder.to_gate()
```

**Function as a custom gate**: A normal Python function can also be used as a custom gate. Instructions can be added to the Circuit in a normal function.

**Condition based on measurements**: In SpinQKit, a Circuit has a measure method to measure some of the qubits and store the result into classical bits. This method inserts a special MEASURE gate into the circuit. After the measurement, a gate can be conditionally applied, and the condition is based on the value of classical bits. Such a flow control is also known as cif. A condition in SpinQKit is a tuple of classical bits, a comparator (==, !=, >, >=, <, <=), and an integer. The | operator is used to add a condition to an instruction. The whole statement will be like ``circuit << instruction | condition``. The MEASURE gate cannot be used in a custom gate or used with cif. Currently, this feature is only supported by the SpinQ simulator.

### 2.2 OpenQASM

Currently, SpinQKit supports OpenQASM 2.0. The basic gates allowed in SpinQKit include id, x, y, z, h, rx, ry, rz, t, tdg, s, sdg, p, cx, cy, cz, swap, ccx, u, U, CX, measure, and barrier. Other gates must be defined. Please notice that a custom gate cannot be called in another custom gate. The measure gate cannot be used in a custom gate either. SpinQKit does not support including other qasm files. If you want to define a custom gate, you must put all the source code in the same file. The include statement will be ignored.

### 2.3 Qiskit

SpinQKit also supports IBM Qiskit Python interface. We include the qiskit.circuit package and some related packages in SpinQKit. Therefore, you can construct a Qiskit QuantumCircuit instance and run it with SpinQKit, even without installing Qiskit. Particularly, SpinQKit has supported QFT, QPE, and Grover primitives in Qiskit (in qiskit.circuit.library) so that you can build up your quantum algorithms based on these primitives. Nevertheless, SpinQKit does not include all the Qiskit code. If you want to use the qiskit.algorithm package and run the circuit on SpinQKit backends, you still need to install Qiskit. In *example/qiskit_hhl_example*.py, we show how to run HHL from qiskit.algorithms.linear_solvers.hhl on the SpinQKit simulator backend. Next, SpinQKit will provide our own algorithm library based on our native Python syntax introduced above.

## 3 Optimization

SpinQKit provides basic circuit optimization features. There are four optimization levels in SpinQKit compilers, corresponding to different combinations of optimization algorithms. 

**Level 0** means no optimization algorithm is applied. 

**Level 1** contains two passes and two algorithms are applied in order. The first one is canceling consecutive redundant gates. If a series of same gates operate on the same qubit(s) and these gates can be removed without affecting the final result, e.g., H and CX, this algorithm will remove these gates from the circuit. If a number of rotation gates rotates the same qubit around the same axis, the algorithm will combine them into one rotation gate. The second algorithm collapses more than 3 consecutive single-qubit gates on the same qubit into several basic gates. The algorithm calculates the matrix that represents these gates and decomposes the matrix to basic gates. Currently, SpinQKit uses ZYZ decomposition. 

**Level 2** contains the two algorithms in Level 1 and then applies a third algorithm. The third algorithm collapses more than 6 consecutive two-qubit gates on the same two qubits into certain Ry, Rz, and CX gates.  The algorithm also calculates the matrix that represents the original gates and then decompose the matrix.

**Level 3** first cancels redundant gates and then applies two optimization algorithms based on quantum state analysis introduced in [https://arxiv.org/abs/2012.07711v1](https://arxiv.org/abs/2012.07711v1). The two algorithms are reported to perform better than the most aggressive optimization level in Qiskit. After the two algorithm, the collapsing single-qubit gates and collapsing two-qubit gates passes are applied.

The optimization features in SpinQKit are still experimental. More algorithms are will be added in the future. Please let us know if you find any issue.
