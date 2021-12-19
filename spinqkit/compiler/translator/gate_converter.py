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

def decompose_single_qubit_gate(gate: Gate, qubits: List, params: List =[]) -> List:
    decomposition = []

    if len(gate.factors) > 0:
        for f in gate.factors:
            plambda = f[2] if len(f)>2 else None
            sub_params = [plambda(params)] if plambda!=None and len(params)>0 else []
            decomposition.append(Instruction(f[0], qubits, [], *sub_params))
    else:
        mat = gate.get_matrix()
        alpha, beta, gamma, phase = decompose_zyz(mat)
        decomposition.append(Instruction(Rz, qubits, [alpha]))
        decomposition.append(Instruction(Ry, qubits, [beta]))
        decomposition.append(Instruction(Rz, qubits, [gamma]))

    return decomposition

def decompose_multi_qubit_gate(gate: Gate, qubits: List, params: List =[]) -> List:
    if isinstance(gate, ControlledGate):
        return decompose_multi_control_gate(gate, qubits, params)    
    elif len(gate.factors) > 0:
        decomposition = []
        for f in gate.factors:
            sub_qubits = [qubits[i] for i in f[1]]
            plambda = f[2] if len(f)>2 else None
            if plambda!=None:
                if len(params) == 0:
                    raise ValueError
                inst_params = [plambda(params)]
                decomposition.append(Instruction(f[0], sub_qubits, [], *inst_params))
            else:
                decomposition.append(Instruction(f[0], sub_qubits, []))

        return decomposition


def decompose_multi_control_gate(gate: ControlledGate, qubits: List, params: List) -> List:
    """ Decompose a multi-qubit controlled gate and return a list of instructions from factor gates.
        The factor gates of a controlled gate is decomposed recursively when the factors function is called.
    """
    decomposition = []

    if gate.subgate in IR.basis_set:
        for f in gate.factors:
            sub_qubits = [qubits[i] for i in f[1]]
            plambda = f[2] if len(f)>2 else None
            if plambda!=None:
                if len(params) == 0:
                    raise ValueError
                inst_params = [plambda(params)]
                decomposition.append(Instruction(f[0], sub_qubits, [], *inst_params))
            else:
                decomposition.append(Instruction(f[0], sub_qubits, []))
    else:
        for f in gate.factors:
            sub_qubits = [qubits[i] for i in f[1]]
            plambda = f[2] if len(f)>2 else None
            sub_params = [plambda(params)] if plambda!=None else []
            if f[0] in IR.basis_set:
                decomposition.append(Instruction(f[0], sub_qubits, [], *sub_params))
            else:
                decomposition.extend(decompose_multi_control_gate(f[0], sub_qubits, sub_params))

    return decomposition