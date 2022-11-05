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
from typing import List, Union, Any
import numpy as np
from spinqkit import get_compiler
from spinqkit.model import Gate, Circuit, GateBuilder, InappropriateBackendError
from spinqkit import Rx, Ry, Rz, CX, I, X, Y, Z
from spinqkit import PauliBuilder, calculate_pauli_expectation, generate_hamiltonian_matrix
from spinqkit.backend import BasicSimulatorBackend
from .optimizer import Optimizer

class VQE(object):
    def __init__(self,
        qubit_num: int,
        depth:int,
        hamiltonian: Union[np.ndarray, List],
        optimizer: Optimizer,
        ansatz: Gate = None,
        ansatz_params: List = None):
        '''
        Hamiltonian is a matrix or a list of (pauli string, coeff). 
        If it is a matrix, the expection value is calculated through matrix multiplication.
        If it is a list, the expection value is calculated through pauli measurements.
        '''
        self.__qubit_num = qubit_num
        self.__depth = depth
        self.__H = hamiltonian
        self.__optimizer = optimizer
        if ansatz is not None:
            self.__ansatz = ansatz
        else:
            self.__ansatz = self._generate_ansatz()
        if ansatz_params is not None:
            self.__ansatz_params = ansatz_params
        else:
            self.__ansatz_params = np.random.uniform(0,2*np.pi,(self.__qubit_num, 3*self.__depth))
        self.__circuit = self._build()

    def _build(self, h: Gate = None) -> Circuit:
        circ = Circuit()
        qubits = circ.allocateQubits(self.__qubit_num)
        param_list = self.__ansatz_params.tolist()
        circ << (self.__ansatz, qubits, param_list)
        return circ

    def _generate_ansatz(self):
        builder = GateBuilder(self.__qubit_num)
        for d in range(self.__depth):
            for q in range(self.__qubit_num):
                xlambda = lambda params, row=q, col = 3*d: params[row][col]
                builder.append(Rx, [q], xlambda)
                zlambda = lambda params, row=q, col = 3*d+1: params[row][col]
                builder.append(Rz, [q], zlambda)
                x2lambda = lambda params, row=q, col = 3*d+2: params[row][col]
                builder.append(Rx, [q], x2lambda)
                # ylambda = lambda params, row=q, col = 2*d: params[row][col]
                # builder.append(Ry, [q], ylambda)
                # zlambda = lambda params, row=q, col = 2*d+1: params[row][col]
                # builder.append(Rz, [q], zlambda)
            for q in range(self.__qubit_num - 1):
                builder.append(CX, [q, q+1])
            builder.append(CX, [self.__qubit_num - 1, 0])
        return builder.to_gate()

    def _generate_hamiltonian_matrix(self):
        if isinstance(self.__H, list):
            return generate_hamiltonian_matrix(self.__H)

        return self.__H

    @property
    def ansatz_params(self):
        return self.__ansatz_params

    def get_circuit(self) -> Circuit:
        '''Return only the ansatz circuit
        '''
        return self.__circuit

    def loss_func(self, params: np.ndarray, backend, config) -> float:
        compiler = get_compiler("native")
        optimization_level = 0
        value = 0.0
        self.__ansatz_params = params.reshape(self.__ansatz_params.shape)
        if isinstance(self.__H, np.ndarray):
            if isinstance(backend, BasicSimulatorBackend):
                self.__circuit = self._build()
                exe = compiler.compile(self.__circuit, optimization_level)
                result = backend.execute(exe, config)
                psi = np.array(result.states)
                value = np.real(psi @ self.__H @ psi.conj().T)
            else:
                raise InappropriateBackendError('Only a simulator backend supports the state calculation.')
        else:
            for pstr, coeff in self.__H:
                part = PauliBuilder(pstr).to_gate()
                part_circ = self._build(part)
                exe = compiler.compile(part_circ, optimization_level)
                result = backend.execute(exe, config)
                value += coeff * calculate_pauli_expectation(pstr, result.probabilities)

        return value

    def gradient(self, params: np.ndarray, backend, config):
            params_p = params.flatten()
            params_m = params.flatten()
            grads = np.ones_like(params_p)
            for i in range(len(params_p)):
                ori_p = params_p[i]
                ori_m = params_m[i]
                params_p[i] = ori_p + np.pi / 2
                params_m[i] = ori_m - np.pi / 2
                grads[i] = (self.loss_func(params_p, backend, config) - self.loss_func(params_m, backend, config)) / 2
                params_p[i] = ori_p
                params_m[i] = ori_m
            return grads.reshape(params.shape)

    def run(self, backend: Any, config: Any, grad_func = None):
        if grad_func is None:
            grad_func = self.gradient
        min_value = self.__optimizer.optimize(self.loss_func, self.__ansatz_params, grad_func, backend, config)
        return min_value


