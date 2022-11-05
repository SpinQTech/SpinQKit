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
from typing import Dict, List, Callable
from spinqkit.algorithm import QAOA
from scipy.optimize import minimize
from spinqkit.model import Gate, GateBuilder
from spinqkit.model import CX, Rz
from spinqkit import get_basic_simulator, BasicSimulatorConfig

# Count the cut
def maxcut_obj(cut_str: str, edges: List) -> int:
    obj = 0
    for i, j in edges:
        if cut_str[i] != cut_str[j]:
            obj -= 1
    return obj

# Compute the max cut expectation
def compute_expectation(counts: Dict, edges: List) -> float:
    avg = 0
    sum_count = 0
    for bitstring, count in counts.items():
        obj = maxcut_obj(bitstring, edges)
        avg += obj * count
        sum_count += count    
    return avg/sum_count

# Create the max cut Hamiltonian for QAOA
def create_problem_hamiltonian(vcount: int, edges: List) -> Gate:
    hp_builder = GateBuilder(vcount)
    plam = lambda params: 2 * params[0]
    for v1, v2 in edges:
        hp_builder.append(CX, [v1, v2])
        hp_builder.append(Rz, [v2], plam)
        hp_builder.append(CX, [v1, v2])
    return hp_builder.to_gate()

# Run QAOA
def get_expectation(vcount: int, edges: List, rep: int) -> Callable:
    engine = get_basic_simulator()
    config = BasicSimulatorConfig()
    config.configure_shots(1024)
    Hp = create_problem_hamiltonian(vcount, edges)
    qaoa_algo = QAOA(vcount, 1, Hp, 1)
    def execute_QAOA(parameters):
        result = qaoa_algo.run(parameters, engine, config)
        cut = max(result.counts, key=result.counts.get)
        print(cut)
        return compute_expectation(result.counts, edges)
    return execute_QAOA


G = [(0,1), (1,2), (2,3), (3,0)]
expectation = get_expectation(4, G, 1)

# Optimize, the max cut should be 1010 or 0101
res = minimize(expectation, 
                      [1.0, 1.0], 
                      method='COBYLA')

