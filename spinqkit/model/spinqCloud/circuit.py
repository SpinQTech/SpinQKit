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

from typing import List
from spinqkit.compiler.ir import NodeType, IntermediateRepresentation
from ..exceptions import CircuitOperationParsingError, CircuitOperationValidationError
from .gate import *
from .platform import *
from typing import Optional
from ..gates import H, CX
from ..instruction import Instruction
import math
from queue import Queue

class CircuitOperation:
    def __init__(self, time_slot: int, gate: Gate, nativeOperation: bool = True, qubits: List = [], arguments: List = []):
        self._time_slot = time_slot
        self._gate = gate
        self._nativeOperation = nativeOperation
        self._qubits = qubits
        self._arguments = arguments

    @property
    def time_slot(self) -> int:
        return self._time_slot

    @property
    def gate(self) -> Gate:
        return self._gate

    @property
    def nativeOperation(self) -> Gate:
        return self._nativeOperation

    @property
    def arguments(self):
        return self._arguments

    @property
    def qubits(self):
        return self._qubits

    def to_dict(self):
        co_dict = {"timeSlot": self._time_slot, "nativeOperation": self._nativeOperation, "gate": self._gate.to_dict(), "qubits": self._qubits, "arguments": self._arguments}
        return co_dict

class Circuit:
    def __init__(self, operations: List[CircuitOperation] = [], definitions: List = []):
        self._operations = operations
        self._definitions = definitions
    
    @property
    def operations(self):
        return self._operations

    @property
    def definitions(self):
        return self._definitions

    def to_dict(self):
        return {"operations": [o.to_dict() for o in self._operations], "definitions": []}

def _topological_sorted_vertex(g):
        vidx_list = g.topological_sorting()
        vs = []
        for vidx in vidx_list:
            vs.append(g.vs[vidx])
        return vs

def _count_qubits(vs):
        count = 0
        for v in vs:
            if v["type"] == NodeType.init_qubit.value:
                count = count + 1
        return count

def convert_cz(v):
    edges = v.in_edges()
    edges.sort(key = lambda k : k.index)
    qubits = []
    clbits = []
    for e in edges:
        if 'qubit' in e.attributes():
            qubits.append(e['qubit'])
        elif 'clbit' in e.attributes():
            clbits.append(e['clbit'])
    subgates = []
    subgates.append(Instruction(H, [qubits[1]], clbits))
    subgates.append(Instruction(CX, qubits, clbits))
    subgates.append(Instruction(H, [qubits[1]], clbits))
    return subgates

def _vertex_to_circuit_operation(circuitboard, name, qubits, arguments) -> CircuitOperation:
    gate = find_gate(name)
    if gate is None:
        raise CircuitOperationParsingError("Gate with name = " + name + " is not support by spinq cloud.")
    arguments = arguments
    largest_slot = 0
    if gate.gtag == 'Barrier':
        qubits = [q+1 for q in qubits]
        # calc the time_slot of the barrier gate
        for q in qubits:
            largest_slot = max(largest_slot, len(circuitboard[q]))
        # append operation to each qubits
        for q in qubits:
            while len(circuitboard[q]) < largest_slot:
                circuitboard[q].append('*')
            circuitboard[q].append(gate.gname)
        # convert to our operation structure
        return  CircuitOperation(largest_slot+1, gate, True, qubits, arguments)
    elif gate.gtag == "C2":  # two-bits gates
        qubits = [qubits[1]+1, qubits[0]+1]
        # get the largest slot involved in this gate, including the qubits between the controller and target
        for row in circuitboard[min(qubits)-1:max(qubits)]:
            largest_slot = max(largest_slot, len(row))
        # append operation to each qubits
        for row_idx in range(min(qubits)-1, max(qubits)):
            row = circuitboard[row_idx]
            while len(row) < largest_slot:
                row.append('*')
            if row_idx == (qubits[1]-1):
                row.append(gate.gname + "_c")
            elif row_idx == (qubits[0]-1):
                row.append(gate.gname + "_t")
            else:
                row.append('|')
        return  CircuitOperation(largest_slot+1, gate, True, qubits, arguments)
    elif gate.gtag == "U1":
        # U(theta, phi, lambda)转化为Rz(phi)Ry(theta)Rz(lambda)
        circuitboard[qubits[0]].append(gate.gname)
        # convert to our operation structure
        theta = round (float(math.degrees(arguments[0])), 1)
        phi = round (float(math.degrees(arguments[1])), 1)
        lam = round (float(math.degrees(arguments[2])), 1)
        qubits = [qubits[0]+1]
        arguments = [theta, phi, lam]
        return  CircuitOperation(len(circuitboard[qubits[0]-1]), gate, True, qubits, arguments)
    elif gate.gtag == "R1":
        # convert to our operation structure
        degree = round (float(math.degrees(arguments[0]))%360, 1)
        circuitboard[qubits[0]].append(gate.gname + " " + str(degree))
        qubits = [qubits[0]+1]
        arguments = [degree]
        return  CircuitOperation(len(circuitboard[qubits[0]-1]), gate, True, qubits, arguments)
    elif gate.gtag in ['C1', 'Measure']:
        circuitboard[qubits[0]].append(gate.gname)
        qubits = [qubits[0]+1]
        return CircuitOperation(len(circuitboard[qubits[0]-1]), gate, True, qubits, arguments)
    else:
        raise CircuitOperationParsingError("Gate with tag = " + gate.gtag + " is not support by spinq cloud.")

# customized operation dictionary
customized_op = {}

def _transfer_qubits(global_qlist, local_qlist):
    return [global_qlist[x] for x in local_qlist]

def _transfer_arguments(global_arguments, local_arguments, func):
    args = [global_arguments[x] for x in local_arguments]
    return func(*args)

def _expand_customized_gate(def_name, sorted_vs, g):
    if sorted_vs is None:
        raise CircuitOperationParsingError("Miss necessary variable sorted vertex list")
    def_v = g.vs.find(def_name, type=2)
    callee_q=Queue(maxsize=0)
    callee_set = set()
    for v in def_v.successors():
        callee_q.put(v)
    while not callee_q.empty():
        item = callee_q.get()
        callee_set.add(item.index)
        for v in item.successors():
            callee_q.put(v)
    sorted_callee_list = [v for v in sorted_vs if v.index in callee_set ]
    return sorted_callee_list

def _customized_vertex_to_circuit_operation(circuitboard, gatename, v) -> CircuitOperation:
    global_qubits = v['qubits']
    global_arguments = v['params']
    callee_list = customized_op[gatename]
    oplist = []
    for g in callee_list:
        sub_qubits = g['qubits']
        final_qubits = _transfer_qubits(global_qubits, sub_qubits)
        final_arguments = []
        if g['params'] is not None and len(g['params']) > 0:
            for p in g['params']:
                if isinstance(p, (int, float)):
                    final_arguments.append(p)
                else:
                    sub_arguments = []
                    if 'pindex' in g.attributes() and g['pindex'] is not None and len(g['pindex']) > 0:
                        sub_arguments = g['pindex']
                    final_arg = _transfer_arguments(global_arguments, sub_arguments, p)
                    final_arguments.append(final_arg)
        op = _vertex_to_circuit_operation(circuitboard, g["name"], final_qubits, final_arguments)
        oplist.append(op)
    return oplist

def _is_valid(operation: CircuitOperation, platform: Platform) -> bool:
    if not platform.has_gate(operation.gate):
        raise CircuitOperationValidationError("This gate " + operation.gate.gname + " does not support by the " + platform.code + " platform.")
    if  operation.gate.gtag == "C2" and ((operation.qubits[0], operation.qubits[1]) not in platform.coupling_map):
        raise CircuitOperationValidationError("Two-bit gate " + operation.gate.gname + " does not follow the topology.")
    if  operation.gate.gtag == "R1" and (operation.arguments[0] < 0 or operation.arguments[0] > 360):
        raise CircuitOperationValidationError("Rotation degree " + operation.arguments[0] + " is invalid, must from 0 to 360.")
    if  operation.gate.gtag == "U1":
        for i in range(3):
            if operation.arguments[i] < 0 or operation.arguments[i] > 360:
                raise CircuitOperationValidationError("Rotation degree " + operation.arguments[i] + " is invalid, must from 0 to 360.")
    return True

def graph_to_circuit(ir: IntermediateRepresentation, platform:Optional[str]=None) -> Circuit:
    global customized_op
    # if platform is not null, validate the circuit with the platform's rule
    p = None
    if platform is not None:
        p = find_platform(platform)
    # all gate vertex sorted by topology
    sorted_vs = _topological_sorted_vertex(ir.dag)
    # get total qubit_size
    qubit_size = _count_qubits(sorted_vs)
    if p is not None and p.max_bitnum < qubit_size:
        raise CircuitOperationValidationError("Register more bits than the platform supplies.")
    # convert each vertex in graph to a circuit operation
    operations = []
    circuitboard = [[] for i in range(qubit_size)]
    for v in sorted_vs:
        if v["type"] == NodeType.op.value:
            arguments = []
            if 'params' in v.attributes() and v['params'] is not None and len(v['params']) > 0:
                arguments = v['params']
            # single gate
            op = _vertex_to_circuit_operation(circuitboard, v['name'], v['qubits'], arguments)
            if p is None or _is_valid(op, p):
                operations.append(op)
        elif v["type"] == NodeType.caller.value:
            # customized gate
            gatename = v["name"]
            if gatename not in customized_op:
                customized_op[gatename] = _expand_customized_gate(gatename, sorted_vs, ir.dag)
            oplist = _customized_vertex_to_circuit_operation(circuitboard, gatename, v)
            if p is not None:
                for op in oplist:
                    if _is_valid(op, p):
                        operations.append(op)
            else:
                operations.extend(oplist)
    # reset customized_op
    customized_op = {}            
    return Circuit(operations=operations)

