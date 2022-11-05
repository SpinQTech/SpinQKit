# Copyright 2021 SpinQ Technology Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import List
import numpy as np
from spinqkit.model import Instruction, Rz, Ry, P, X, GateBuilder
from spinqkit.compiler.decomposer import decompose_zyz, decompose_two_qubit_gate, build_gate_for_isometry

Ph_bulider = GateBuilder(1)

Ph_bulider.append(P, [0], lambda params: params[0])
Ph_bulider.append(X, [0])
Ph_bulider.append(P, [0], lambda params: params[0])
Ph_bulider.append(X, [0])

Ph = Ph_bulider.to_gate()

def generate_vector_encoding(vector: np.ndarray, qubits: List) -> List[Instruction]:
    if len(vector.shape) == 1:
        vector = vector.reshape(vector.shape[0], 1)

    nb = int(np.log2(len(vector)))
    if nb != len(qubits):
        raise ValueError
    vector = vector / np.linalg.norm(vector)

    inst_list = []
    if len(qubits) == 1:
        mat = np.array([[vector.item(0, 0), -np.conjugate(vector.item(1, 0))], [vector.item(1, 0), np.conjugate(vector.item(0, 0))]])/np.sqrt(abs(vector.item(0, 0))**2 + abs(vector.item(1,0))**2)
        alpha, beta, gamma, phase = decompose_zyz(mat)

        _EPS = 1e-10
        if abs(alpha - 0.0) > _EPS:
            inst_list.append(Instruction(Rz, qubits, [], alpha))
        if abs(beta - 0.0) > _EPS:
            inst_list.append(Instruction(Ry, qubits, [], beta))
        if abs(gamma - 0.0) > _EPS:
            inst_list.append(Instruction(Rz, qubits, [], gamma))
        if abs(phase - 0.0) >= _EPS:
            inst_list.append(Instruction(Ph, qubits, [], phase))
    else:
        gate = build_gate_for_isometry(vector)
        inst_list.append(Instruction(gate, qubits[::-1]))

    return inst_list