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
from typing import Dict, List
from spinqkit import I, Z, X, Y
import numpy as np
from functools import reduce
import itertools

def calculate_pauli_expectation(pauli_string: str, probabilities: Dict) -> float:
    imat = I.matrix()
    zmat = Z.matrix()
    zerovec = np.array([[1], [0]])
    onevec = np.array([[0], [1]])

    umat = 1
    for ch in pauli_string:
        if ch.capitalize() in ['X', 'Y', 'Z']:
            umat = np.kron(zmat, umat)
        elif ch.capitalize() == 'I':
            umat = np.kron(imat, umat)
        else:
            raise ValueError('The input string is not a Pauli string')

    expect_value = 0.0
    for bit_string in probabilities.keys():
        dlist = []
        vec = 1
        for digit in bit_string:
            if digit == '0':
                vec = np.kron(zerovec, vec)
            else:
                vec = np.kron(onevec, vec)

        prod = umat.dot(vec)
        if np.allclose(vec, prod):
            expect_value += 1 * probabilities[bit_string]
        else:
            expect_value += -1 * probabilities[bit_string]
    
    return expect_value

def generate_hamiltonian_matrix(pauli_string_list: List):
    imat = I.matrix()
    xmat = X.matrix()
    ymat = Y.matrix()
    zmat = Z.matrix()

    qubit_num = len(pauli_string_list[0][0])
    ham_mat = np.zeros((2 ** qubit_num, 2 ** qubit_num), dtype=np.complex64)

    for pauli_string, coeffi in pauli_string_list:
        umat = []
        for ch in pauli_string:
            if ch.capitalize() == 'Z':
                umat.append(zmat)
            elif ch.capitalize() == 'I':
                umat.append(imat)
            elif ch.capitalize() == 'Y':
                umat.append(ymat)
            elif ch.capitalize() == 'X':
                umat.append(xmat)
        ham_mat += coeffi * reduce(np.kron, umat)
    return ham_mat
