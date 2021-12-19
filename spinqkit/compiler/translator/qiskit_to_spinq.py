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

from typing import Dict, List, Tuple, Optional
from math import pi
import qiskit.circuit as qqc
from spinqkit.model.gates import * 
from spinqkit.model import Circuit, UnsupportedQiskitInstructionError

basis_map = {'id': I, 'h': H, 'x': X, 'y': Y, 'z': Z, 'rx': Rx, 'ry': Ry, 'rz': Rz, 't': T, 'tdg': Td, 's': S, 'sdg': Sd, 'p': P, 'cx': CX, 'cy': CY, 'cz': CZ, 'swap': SWAP, 'ccx': CCX, 'u': U, 'measure': MEASURE}

def qiskit_to_spinq(qc: qqc.QuantumCircuit) -> Circuit:
    circ = Circuit()
    qreg_map = {}
    creg_map = {}

    for register in qc.qregs:
        tmp = circ.allocateQubits(register.size)
        qreg_map[register.name] = tmp

    for register in qc.cregs:
        tmp = circ.allocateClbits(register.size)
        creg_map[register.name] = tmp

    add_instruction(qc, circ, qreg_map, creg_map)
    return circ

def add_instruction(qc: qqc.QuantumCircuit, circ: Circuit, qreg_map: Dict, creg_map: Dict, qubits: Optional[List] = None, condition: Optional[Tuple] = None):
    """
        Args:
        qubits: for recursive conversion, None at first.
        condition: for recursive conversion, None at first.
    """
    ctl_count = 0
    for reg in qc.qregs:
        if reg.name == 'control':
            ctl_count += reg.size
   
    for instruction, qargs, cargs in qc.data:
        if instruction.condition != None:
            classical = instruction.condition[0]
            if isinstance(classical, qqc.Clbit):
                clbits = [creg_map[classical.register.name][classical.index]]
            else:
                clbits = creg_map[classical.name]
            condition = (clbits, '==', int(instruction.condition[1]))        

        if not isinstance(instruction, (qqc.Gate, qqc.Instruction, qqc.Measure, qqc.Barrier)):
            raise UnsupportedQiskitInstructionError
        
        if qubits == None: 
            sub_qubits = qargs
        else:
            if isinstance(instruction, qqc.ControlledGate):
                sub_qubits = []
                for q in qargs:
                    if q.register.name == 'control':
                        sub_qubits.append(qubits[q.index])
                    else:
                        sub_qubits.append(qubits[q.index + ctl_count])
            else:
                sub_qubits = [qubits[q.index + ctl_count] for q in qargs]

        if instruction.name in basis_map.keys():
            gate = basis_map[instruction.name]        
            qlist = [qreg_map[arg.register.name][arg.index] for arg in sub_qubits]
            if cargs != None:
                clist = [creg_map[arg.register.name][arg.index] for arg in cargs]
            params = instruction.params
            
            if params != None and len(params) > 0:
                if condition != None:
                    circ<< (gate, qlist, *params) | condition
                else:
                    circ<< (gate, qlist, *params)
            else:    
                if condition != None:
                    if gate == MEASURE:
                        raise UnsupportedQiskitInstructionError('Measure cannot be conditional.')
                    circ<< (gate, qlist) | condition
                else:
                    if gate == MEASURE:
                        circ.measure(qlist, clist)
                    else:
                        circ<< (gate, qlist)
        elif isinstance(instruction, qqc.Barrier):
            continue
        else:
            add_instruction(instruction.definition, circ, qreg_map, creg_map, sub_qubits, condition)
        
        