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

from spinqkit import get_basic_simulator, get_compiler, BasicSimulatorConfig
from spinqkit import Circuit, GateBuilder, ControlledGate, QuantumRegister
from spinqkit import SWAP, H, X, CP

import numpy as np
from fractions import Fraction
from math import gcd
import random

def create_control_u(a, power):
    amod15_builder = GateBuilder(4)
    for iteration in range(power):
        if a in [2,13]:
            amod15_builder.append(SWAP, [0,1])
            amod15_builder.append(SWAP, [1,2])
            amod15_builder.append(SWAP, [2,3])
        if a in [7,8]:
            amod15_builder.append(SWAP, [2,3])
            amod15_builder.append(SWAP, [1,2])
            amod15_builder.append(SWAP, [0,1])
        if a == 11:
            amod15_builder.append(SWAP, [1,3])
            amod15_builder.append(SWAP, [0,2])
        if a in [7,11,13]:
            for q in range(4):
                amod15_builder.append(X, [q])    
    amod15 = amod15_builder.to_gate()
    c_amod15 = ControlledGate(amod15)
    return c_amod15

def qft_dagger(circ: Circuit, qreg: QuantumRegister, n: int):
    for qubit in range(n//2):
        circ << (SWAP, (qreg[qubit], qreg[n-qubit-1]))
    for j in range(n):
        for m in range(j):
            circ << (CP, (qreg[m], qreg[j]), -np.pi/float(2**(j-m)))
        circ << (H, qreg[j])

def qpe_amod15(a):
    n_count = 8
    circ = Circuit()
    qreg = circ.allocateQubits(4+n_count)
    
    for q in range(n_count):
        circ << (H, qreg[q])
    circ << (X, qreg[3+n_count])

    for q in range(n_count):
        qarg = [qreg[q]] + [qreg[i+n_count] for i in range(4)]
        circ << (create_control_u(a, 2**q), qarg)

    qft_dagger(circ, qreg, n_count)

    engine = get_basic_simulator()
    comp = get_compiler("native")

    exe = comp.compile(circ, 0)
    
    config = BasicSimulatorConfig()
    config.configure_shots(1024)
    config.configure_measure_qubits(list(range(n_count)))

    result = engine.execute(exe, config)
    reading = result.get_random_reading()

    phase = int(reading[::-1], 2) / (2**n_count)
    print('reading: ' + reading)
    print('phase: ' + str(phase))
    return phase

N = 15
a = 7
factor_found = False
attempt = 0

while not factor_found and attempt < 10:
    attempt += 1
    phase = qpe_amod15(a)
    frac = Fraction(phase).limit_denominator(N)
    r = frac.denominator
    print("Order: r = %i" % r)
    if phase != 0:
        guesses = [gcd(a**(r//2)-1, N), gcd(a**(r//2)+1, N)]
        for guess in guesses:
            if guess not in [1,N] and (N % guess) == 0: # Check to see if guess is a factor
                print("*** Non-trivial factor found: %i ***" % guess)
                factor_found = True

