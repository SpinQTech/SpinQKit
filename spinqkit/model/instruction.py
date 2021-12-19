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

from typing import List, Tuple
from .basic_gate import Gate
from .gates import MEASURE
import enum

class Instruction(object):
    def __init__(self, gate: Gate, qubits: List[int] = [], clbits: List[int] = [], *params: Tuple):
        self.gate = gate
        self.qubits = qubits
        self.clbits = clbits
        self.params = list(params)
        self.condition = None

        if len(qubits) > gate.qubit_num:
            raise ValueError
    
    def set_condition(self, clbits: List, symbol: str, constant: int):
        self.condition = (clbits, symbol, constant)

    def get_op(self) -> str:
        return self.gate.label