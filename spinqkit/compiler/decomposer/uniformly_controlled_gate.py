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
import numpy as np
import cmath
from spinqkit.model import Gate, GateBuilder, Ry, Rz, H, CX
from spinqkit.compiler.decomposer import decompose_zyz
from spinqkit.model.gates import P
from .diagonal import generate_diagnoal_gates

_EPS = 1e-10

def _demultiplex(g0, g1):
    x = g0.dot(g1.conjugate().T)
    det_x = np.linalg.det(x)
    x11 = x.item((0, 0)) / cmath.sqrt(det_x)
    phi = cmath.phase(det_x)
    r1 = cmath.exp(1j / 2 * (np.pi / 2 - phi / 2 - cmath.phase(x11)))
    r2 = cmath.exp(1j / 2 * (np.pi / 2 - phi / 2 + cmath.phase(x11) + np.pi))
    r = np.array([[r1, 0], [0, r2]], dtype=complex)
    d, u = np.linalg.eig(r.dot(x).dot(r))
        
    if abs(d[0] + 1j) < _EPS:
        d = np.flip(d, 0)
        u = np.flip(u, 1)
    d = np.diag(np.sqrt(d))
    v = d.dot(u.conjugate().T).dot(r.conjugate().T).dot(g1)
    return v, u, r

def _decompose_ucg(unitary_list: np.ndarray, qnum: int) -> Tuple[np.ndarray, np.ndarray]:
    gates = [g.astype(complex) for g in unitary_list]
    diag = np.ones(2 ** qnum, dtype=complex)
    ctrls = qnum - 1
    for step in range(ctrls):
        ucg_count = 2 ** step
        for index in range((ucg_count)):
            size = 2 ** (ctrls - step)
            for i in range(int(size/2)):
                delta = index * size
                idx0 = delta+i
                idx1 = delta+i+size//2
                g0, g1, r = _demultiplex(gates[idx0], gates[idx1])
                gates[idx0] = g0
                gates[idx1] = g1
                rz_mat = Rz.matrix([-np.pi / 2])
                if index < ucg_count - 1:
                    j = delta + i + size
                    gates[j] = gates[j].dot(r.conjugate().T) * rz_mat.item((0, 0))
                    j += size//2
                    gates[j] = gates[j].dot(r) * rz_mat.item((1, 1))
                else:
                    for inner_index in range(ucg_count):
                        inner_delta = inner_index * size
                        # ctr = r.conjugate().T
                        ctr = np.transpose(np.conjugate(r))
                        j = 2 * (inner_delta + i)
                        diag[j] = diag[j] * ctr.item((0, 0)) * rz_mat.item((0, 0))
                        diag[j+1] = diag[j+1] * ctr.item((1, 1)) * rz_mat.item((0, 0))
                        j += size
                        diag[j] *= r.item((0, 0)) * rz_mat.item((1, 1))
                        diag[j+1] *= r.item((1, 1)) * rz_mat.item((1, 1))

    return gates, diag
                    
def _count_trailing_zero(value: int):
    sz = int(np.log2(value)) + 1
    count = 0
    for i in range(sz):
        if (value>>i) & 1 == 1:
            break
        count += 1
    return count

def generate_ucg_diagonal(unitary_list: List, up_to_diag: bool) -> Tuple[Gate, List]:
    ctrl_num = int(np.log2(len(unitary_list)))
    qubit_num = ctrl_num + 1
    # if ctrl_num < 0 or not ctrl_num.is_integer() or ctrl_num != qubit_num - 1:
    #     raise ValueError('The size of unitary_list does not match the size of qubits.')
    
    ucg_builder = GateBuilder(qubit_num)
    if ctrl_num == 0:
        diag = np.ones(2 ** qubit_num).tolist()
        alpha, beta, gamma, _ = decompose_zyz(unitary_list[0])    
        if abs(alpha - 0.0) > _EPS:
            ucg_builder.append(Rz, [0], alpha)
        if abs(beta - 0.0) > _EPS:
            ucg_builder.append(Ry, [0], beta)
        if abs(gamma - 0.0) > _EPS:
            ucg_builder.append(Rz, [0], gamma)
        return ucg_builder.to_gate(), diag

    sub_gates, diag = _decompose_ucg(unitary_list, qubit_num)
    target = 0
    controls = list(range(1, qubit_num))
    h_mat = H.matrix()
    rz_mat = Rz.matrix([-np.pi/2])
    for i in range(len(sub_gates)):
        gate = sub_gates[i]
        if i == 0:
            umat = h_mat.dot(gate)
        elif i == len(sub_gates) - 1:
            umat = gate.dot(rz_mat).dot(h_mat)
        else:
            umat = h_mat.dot(gate.dot(rz_mat)).dot(h_mat)
        alpha, beta, gamma, _ = decompose_zyz(umat)
        ucg_builder.append(Rz, [target], alpha)
        ucg_builder.append(Ry, [target], beta)
        ucg_builder.append(Rz, [target], gamma)

        ctrl_index = _count_trailing_zero(i + 1)
            
        if not i == len(sub_gates) - 1:
            ucg_builder.append(CX, [controls[ctrl_index], target])

    if not up_to_diag:
        diag_gate = generate_diagnoal_gates(diag)
        ucg_builder.append(diag_gate, list(range(qubit_num)))

    return ucg_builder.to_gate(), diag    