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
from spinqkit.model import *
from ..decomposer.ZYZdecomposer import decompose_zyz
from ..ir import IntermediateRepresentation as IR
import numpy as np

def is_primary_gate(gate: Gate):
    if gate in IR.basis_set:
        return True
    elif isinstance(gate, MatrixGate):
        return True
    elif isinstance(gate, ControlledGate) and (isinstance(gate.base_gate, MatrixGate) or 
                gate.base_gate in IR.basis_set):
        return True
    elif isinstance(gate, InverseGate) and (isinstance(gate.base_gate, MatrixGate) or
                gate.base_gate in IR.basis_set):
        return True
    return False

def decompose_single_qubit_gate(gate: Gate, qubits: List, params: List =[]) -> List:
    decomposition = []

    if len(gate.factors) > 0:
        for f in gate.factors:
            plambda = f[2] if len(f)>2 else None
            sub_params = [plambda(params)] if plambda!=None else []
            if is_primary_gate(f[0]):
                decomposition.append(Instruction(f[0], qubits, [], *sub_params))
            else:
                decomposition.extend(decompose_single_qubit_gate(f[0], qubits, sub_params))
    else:
        mat = gate.get_matrix(*params)
        if mat is None:
            raise UnsupportedGateError(gate.label + ' is not supported. Its matrix representation is None.')
        alpha, beta, gamma, phase = decompose_zyz(mat)
        decomposition.append(Instruction(Rz, qubits, alpha))
        decomposition.append(Instruction(Ry, qubits, beta))
        decomposition.append(Instruction(Rz, qubits, gamma))

    return decomposition

def decompose_multi_qubit_gate(gate: Gate, qubits: List, params: List =[]) -> List:
    if len(gate.factors) > 0:
        decomposition = []
        for f in gate.factors:
            sub_qubits = [qubits[i] for i in f[1]]
            plambda = f[2] if len(f)>2 else None
            sub_params = [plambda(params)] if plambda is not None else []
            if is_primary_gate(f[0]):
                decomposition.append(Instruction(f[0], sub_qubits, [], *sub_params))
            elif f[0].qubit_num == 1:
                decomposition.extend(decompose_single_qubit_gate(f[0], sub_qubits, sub_params))
            else:
                decomposition.extend(decompose_multi_qubit_gate(f[0], sub_qubits, sub_params))
        return decomposition

    raise UnsupportedGateError(gate.label + ' is not supported.')