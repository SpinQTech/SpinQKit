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
from typing import List, Optional, Union
import numpy as np
from spinqkit import get_compiler
from spinqkit.model import Gate, Circuit, RepeatBuilder, H, Rx

class QAOA(object):
    def __init__(
        self, 
        qubit_num: int,
        step: int,
        problem: Gate,
        problem_param_num: int, 
        init_state_gate: Gate = None, 
        mixer: Gate = None,
        mixer_param_num: int = 1):
        
        self.__qubit_num = qubit_num
        self.__step = step
        self.__problem = problem

        if self.__problem.qubit_num != qubit_num:
            raise ValueError('The qubit number in hamiltonian should be the same with the argument qubit_num.')
        self.__problem_param_num = problem_param_num

        if init_state_gate is not None:
            if init_state_gate.qubit_num != qubit_num:
                raise ValueError('The qubit number in init_state_gate should be the same with the argument qubit_num.')
            self.__init_state_gate = init_state_gate
        else:
            self.__init_state_gate = self._prepare_init_state()
        if mixer is not None:
            if mixer.qubit_num != qubit_num:
                raise ValueError('The qubit number in mixer should be the same with the argument qubit_num.')
            self.__mixer = mixer
        else:
            self.__mixer = self._generate_mixer()
        self.__mixer_param_num = mixer_param_num

    def _prepare_init_state(self):
        init_builder = RepeatBuilder(H, self.__qubit_num)
        return init_builder.to_gate()

    def _generate_mixer(self):
        plam = lambda params: 2 * params[0]
        rbuilder = RepeatBuilder(Rx, self.__qubit_num, plam)
        return rbuilder.to_gate()

    def _build(self, params: List) -> Circuit:
        circ = Circuit()
        qubits = circ.allocateQubits(self.__qubit_num)
        circ << (self.__init_state_gate, qubits)
        if len(params) != (self.__mixer_param_num + self.__problem_param_num) * self.__step:
            raise ValueError('The number of parameters is not right')
        beta = params[: self.__mixer_param_num * self.__step]
        gamma = params[self.__mixer_param_num * self.__step:]
        for i in range(self.__step):
            circ << (self.__problem, qubits, gamma[i])
            circ << (self.__mixer, qubits, beta[i])

        return circ

    def run(self, parameters, backend, config):
        compiler = get_compiler("native")
        optimization_level = 0
        circ = self._build(parameters)
        exe = compiler.compile(circ, optimization_level)
        result = backend.execute(exe, config)
        return result

