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

from spinqkit.compiler.compiler import Compiler
from spinqkit.model import Circuit, Instruction
from spinqkit.model import UnsupportedGateError
from .ir import IntermediateRepresentation, NodeType
from .translator.gate_converter import decompose_single_qubit_gate, decompose_multi_qubit_gate
from .optimizer import PassManager

class NativeCompiler(Compiler):
    def __init__(self):
        pass

    def compile(self, circ: Circuit, level: int) -> IntermediateRepresentation:
        ir = IntermediateRepresentation()
        qnum = 0
        for qlen in circ.qureg_list:
            ir.add_init_nodes(qnum, qlen, NodeType.init_qubit)
            qnum += qlen
        
        cnum = 0
        for clen in circ.clreg_list:
            ir.add_init_nodes(cnum, clen, NodeType.init_clbit)
            cnum += clen

        for inst in circ.instructions:
            gate = inst.gate
            if gate in IntermediateRepresentation.basis_set:
                vindex = ir.add_op_node(inst.get_op(), inst.params, inst.qubits, inst.clbits)
                if inst.condition != None:
                    ir.add_node_condition(vindex, inst.condition[0], inst.condition[1], inst.condition[2])
            else:
                if gate.qubit_num == 1:
                    ilist = decompose_single_qubit_gate(gate, inst.qubits, inst.params)
                else:
                    ilist = decompose_multi_qubit_gate(gate, inst.qubits, inst.params)
                
                if len(ilist) == 0:
                    raise UnsupportedGateError("The gate " + gate.label + " is not supported.")
                for i in ilist:
                    ir.add_op_node(i.get_op(), i.params, i.qubits, i.clbits)

        ir.build_dag()
        
        manager = PassManager(level)
        manager.run(ir)
        return ir