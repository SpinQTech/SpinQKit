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

from spinqkit.model.gates import MEASURE
from typing import List, Tuple, Union
from .basic_gate import Gate
from .instruction import Instruction
from .register import QuantumRegister, ClassicalRegister

class Circuit(object):
    def __init__(self):
        self.__qubits_num = 0
        self.__clbits_num = 0
        self.__qureg_list = []
        self.__clreg_list = []
        self.__instructions = []

    @property
    def qubits_num(self):
        return self.__qubits_num

    @property
    def clbits_num(self):
        return self.__clbits_num

    @property
    def qureg_list(self):
        return self.__qureg_list

    @property
    def clreg_list(self):
        return self.__clreg_list

    @property
    def instructions(self):
        return self.__instructions

    def allocateQubits(self, num: int):    
        reg = QuantumRegister(num, self.__qubits_num)
        self.__qureg_list.append(num)
        self.__qubits_num += num
        return reg

    def allocateClbits(self, num: int):
        reg = ClassicalRegister(num, self.__clbits_num)
        self.__clreg_list.append(num)
        self.__clbits_num += num
        return reg

    def __lshift__(self, other: Tuple):
        if isinstance(other[1], tuple):
            qubits = list(other[1])
        elif isinstance(other[1], list):
            qubits = other[1]
        else:
            qubits = [other[1]]
        
        self.append(other[0], qubits, [], *(other[2:]))
        return self

    def __or__(self, other: Tuple):
        self.__instructions[-1].set_condition(other[0], other[1], other[2])

    def measure(self, qubits: Union[int, List[int]], clbits: Union[int, List[int]]):
        if isinstance(qubits, int):
            qubits = [qubits]
        if isinstance(clbits, int):
            clbits = [clbits]
        if len(qubits) != len(clbits):
            raise Exception('The number of qubits does not match the number of classical bits.')
        self.__instructions.append(Instruction(MEASURE, qubits, clbits))
        

    def append(self, gate: Gate, qubits: List[int] = [], clbits: List[int] = [], *params: Tuple):
        self.__instructions.append(Instruction(gate, qubits, clbits, *params))

    def append_instruction(self, inst: Instruction):
        self.__instructions.append(inst)

    def extend(self, inst_list: List):
        for inst in inst_list:
            self.append_instruction(inst)