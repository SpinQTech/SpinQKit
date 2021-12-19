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

from typing import Tuple, List, Union, Callable
import numpy as np

class Gate(object):
    def __init__(self, label: str, qubit_num: int) -> None:
        self.__label = label
        self.__qubit_num = qubit_num
        self.__factors = []
        self.__matrix = None   

    @property
    def label(self) -> str:
        return self.__label

    @property
    def qubit_num(self) -> int:
        return self.__qubit_num

    @property
    def factors(self) -> List:
        return self.__factors

    @property
    def matrix(self):
        return self.__matrix

    @matrix.setter
    def matrix(self, func):
        self.__matrix = func

    def get_matrix(self, *params: Tuple) -> np.ndarray:
        if self.__matrix == None:
            return None

        if len(params) > 0:
            mat = self.__matrix(params)
        else:
            mat = self.__matrix(0)

        if not np.allclose(np.eye(len(mat)), mat.dot(mat.T.conj())):
            raise ValueError("The gate matrix must be unitary.")

        return mat

class GateBuilder(object):
    """ Build a compound gate
        The factors list contains each subgate and the indexes of qubits it will use.
        The param_lambda uses the whole super parameter list to calculate the parameters of a subgate.
        The param_lambda could be None.
    """
    def __init__(self, qubit_num: int) -> None:
        gate_name = str(id(self)) + '_' + str(qubit_num)
        self.__gate = Gate(gate_name, qubit_num)

    def append(self, gate: Gate, qubits: List, param_lambda: Union[float,Callable] = None):
        if isinstance(param_lambda, float):
            param_lambda = eval('lambda *args: ' + str(param_lambda))
        self.__gate.factors.append((gate, qubits, param_lambda))

    def to_gate(self):
        return self.__gate