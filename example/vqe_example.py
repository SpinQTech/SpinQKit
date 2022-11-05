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

from spinqkit.algorithm import VQE, ADAM
from spinqkit import get_basic_simulator, BasicSimulatorConfig, generate_hamiltonian_matrix
import numpy as np

J = 1.5
Bu = 0.6

ham = []
ham.append(("ZZIIII", J))
ham.append(("IZZIII", J))
ham.append(("ZIIZII", J))
ham.append(("IZIIZI", J))
ham.append(("IIZIIZ", J))
ham.append(("IIIZZI", J))
ham.append(("IIIIZZ", J))
ham.append(("ZIIIII", Bu))
ham.append(("IZIIII", Bu))
ham.append(("IIZIII", Bu))
ham.append(("IIIZII", Bu))
ham.append(("IIIIZI", Bu))
ham.append(("IIIIIZ", Bu))


optimizer = ADAM(maxiter=200, verbose=True)

engine = get_basic_simulator()
config = BasicSimulatorConfig()
config.configure_shots(1024)

# VQE using the Pauli decomposition is very slow on a classical simulator.
# solver = VQE(6, 4, ham, optimizer)
# min = solver.run(engine, config)
# print(min)

mat = generate_hamiltonian_matrix(ham)
print(mat.tolist())

solver = VQE(6, 4, mat, optimizer)

min = solver.run(engine, config)
print(min)

