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

from spinqkit.model.gates import MEASURE
from typing import Dict, List
from math import pi
from .Qasm2Listener import Qasm2Listener
from .Qasm2Parser import *
from ..translator import basis_map
from ..ir import IntermediateRepresentation, NodeType

import traceback

class Qasm2EventListener(Qasm2Listener):
    def __init__(self, ir:IntermediateRepresentation,
    gate_sym_table: Dict[str, int], param_num_table: Dict[str, int] = {}):
        self.ir = ir
        self.gate_sym_table = gate_sym_table
        self.param_num_table = param_num_table
        self.qregister_table = {}
        self.cregister_table = {}
        self.local_qubits = {}
        self.local_params = {}
        self.branching = False
        self.conditional_gates = []
        self.errors = []
        self.total_qubits = 0
        self.total_clbits = 0

    def exitQuantumDeclaration(self, ctx:Qasm2Parser.QuantumDeclarationContext):        
        try:
            id = ctx.Identifier()
            des_ctx = ctx.designator()
            exp_ctx = des_ctx.expression()
            exp_term_ctx = exp_ctx.expressionTerminator()
            index = exp_term_ctx.Integer()
            reg_size = int(index.getText())
            self.qregister_table[id.getText()] = [self.total_qubits+i for i in range(reg_size)]   
            self.ir.add_init_nodes(self.total_qubits, reg_size, NodeType.init_qubit)
            self.total_qubits += reg_size
        except Exception as e:
            self.errors.append(ctx.start.line)

    def exitBitDeclaration(self, ctx:Qasm2Parser.BitDeclarationContext):
        try:
            id = ctx.Identifier()
            des_ctx = ctx.designator()
            exp_ctx = des_ctx.expression()
            exp_term_ctx = exp_ctx.expressionTerminator()
            index = exp_term_ctx.Integer()
            reg_size = int(index.getText())
            self.cregister_table[id.getText()] = [self.total_clbits+i for i in range(reg_size)]
            self.ir.add_init_nodes(self.total_clbits, reg_size, NodeType.init_clbit)
            self.total_clbits += reg_size
        except Exception as e:
            self.errors.append(ctx.start.line)
    
    def exitQuantumGateSignature(self, ctx:Qasm2Parser.QuantumGateSignatureContext):
        try:
            gate_name_ctx = ctx.Identifier()
            gate_name = gate_name_ctx.getText()
            if gate_name in self.gate_sym_table:
                raise Exception('Gate already exists')

            qargs_ctx = ctx.identifierList()
            qargs_list = qargs_ctx.Identifier()
            self.gate_sym_table[gate_name] = len(qargs_list)
            for index in range(len(qargs_list)):
                self.local_qubits[qargs_list[index].getText()] = index
            
            param_ctx = ctx.quantumGateParameter()
            if param_ctx != None:
                param_list_ctx = param_ctx.identifierList()
                param_list = param_list_ctx.Identifier()
                self.param_num_table[gate_name_ctx.getText()] = len(param_list)
                for index in range(len(param_list)):
                    self.local_params[param_list[index].getText()] = index

            self.ir.add_def_node(gate_name_ctx.getText(), 
                                len(self.local_params), 
                                len(self.local_qubits), 0)

        except Exception as e:
            traceback.print_exc()
            self.errors.append(ctx.start.line)
        

    def exitQuantumGateDefinition(self, ctx:Qasm2Parser.QuantumGateDefinitionContext):
        self.local_qubits.clear()
        self.local_params.clear()

    def collectExpressionTerminators(self, ctx:ParserRuleContext):
        terminators = []
        while ctx.getChildCount() == 1:
            ctx = ctx.getChild(0)

        count = ctx.getChildCount()    
        if count == 0:
            if ctx.getText() in self.local_params:
                terminators.append(ctx.getText())
            return terminators

        for i in range(count):
            child = ctx.getChild(i)
            terminators.extend(self.collectExpressionTerminators(child))

        # print(terminators)
        return terminators

    def exitQuantumGateCall(self, ctx:Qasm2Parser.QuantumGateCallContext):
        try:
            gate_name_ctx = ctx.quantumGateName()
            gate_name = gate_name_ctx.getText()

            # check if the gate is declared
            if not gate_name in self.gate_sym_table:
                raise Exception('Unknow gate')
            
            # check the parameters like theta or constants 
            if not gate_name in self.param_num_table and ctx.expressionList() != None:
                raise Exception(f'Gate {gate_name} has no parameter')

            gate_params = []
            param_index = []
            if gate_name in self.param_num_table:
                param_ctx = ctx.expressionList()
                if param_ctx == None:
                    raise Exception('Missing gate parameter')
                param_list = param_ctx.expression()
                if self.param_num_table[gate_name] != len(param_list):
                    raise Exception(f'The number of gate parameter should be {self.param_num_table[gate_name]}')

                for p in param_list:
                    pexp = p.getText()
                    if len(self.local_params) > 0:
                        ptlist = self.collectExpressionTerminators(p)
                        if len(ptlist) > 0:
                            argstr = ','.join(ptlist)
                            lexp = "lambda " + argstr + ": " + pexp
                            # print(lexp)
                            param_index.extend([self.local_params[pt] for pt in ptlist])
                        else:
                            lexp = "lambda *args: " + pexp
                            param_index.append(-1)
                        gate_params.append(eval(lexp))
                    else:
                        gate_params.append(eval(pexp))
            
            # check the qargs
            index_id_list_ctx = ctx.indexIdentifierList()
            index_id_list = index_id_list_ctx.indexIdentifier()
            if self.gate_sym_table[gate_name] != len(index_id_list):
                raise Exception(f'The qubit number of gate {gate_name} should be {self.gate_sym_table[gate_name]}')

            gate_qargs = []
            if len(self.local_qubits) > 0:
                for index_id_ctx in index_id_list:
                    id = index_id_ctx.Identifier().getText()
                    if not id in self.local_qubits:
                        raise Exception('Unknown qubit argument')
                    gate_qargs.append(self.local_qubits[id])

                if gate_name.lower() in basis_map.keys():    
                    vindex = self.ir.add_callee_node(basis_map[gate_name.lower()].label, gate_params, gate_qargs, [], param_index)
                else:
                    vindex = self.ir.add_caller_node(gate_name, gate_params, gate_qargs, [], param_index) # call another custom function
                if self.branching:
                    self.conditional_gates.append(vindex)
            else:                
                duplicates = set()
                for index_id_ctx in index_id_list:
                    id = index_id_ctx.Identifier().getText()
                    if not id in self.qregister_table:
                        raise Exception('Unknown qubit register')

                    exp_list_ctx = index_id_ctx.expressionList()
                    exp_list = exp_list_ctx.expression()
                    if len(exp_list) > 1:
                        raise Exception('Illegal register index')

                    index_ctx = exp_list[0].expressionTerminator()
                    index = int(index_ctx.getText())

                    id_index = index_id_ctx.getText()
                    if id_index in duplicates:
                        raise Exception('The register index is duplicated')
                    else:
                        duplicates.add(id_index)
                    
                    qubits = self.qregister_table[id]
                    if index < 0 or index >= len(qubits):
                        raise Exception('The register index is out of range')
                    gate_qargs.append(qubits[index])
                
                if gate_name.lower() in basis_map.keys():
                    vindex = self.ir.add_op_node(basis_map[gate_name.lower()].label, gate_params, gate_qargs, [])
                else:
                    vindex = self.ir.add_caller_node(gate_name, gate_params, gate_qargs, [], [])
                if self.branching:
                    self.conditional_gates.append(vindex)
        except Exception as e:
            traceback.print_exc()
            self.errors.append(ctx.start.line)

    def exitQuantumMeasurementAssignment(self, ctx: Qasm2Parser.QuantumMeasurementAssignmentContext):
        gate_qargs = []
        gate_cargs = []
        duplicates = set()
        
        try:
            quantumMeasurementCtx = ctx.quantumMeasurement()
            qindex_id_list_ctx = quantumMeasurementCtx.indexIdentifierList()
            qindex_id_list = qindex_id_list_ctx.indexIdentifier()
            
            for index_id_ctx in qindex_id_list:
                id = index_id_ctx.Identifier().getText()
                if not id in self.qregister_table:
                    raise Exception('Unknown qubit register')

                qubits = self.qregister_table[id]
                exp_list_ctx = index_id_ctx.expressionList()
                if exp_list_ctx != None:
                    exp_list = exp_list_ctx.expression()
                    if len(exp_list) > 1:
                        raise Exception('Illegal register index')

                    index_ctx = exp_list[0].expressionTerminator()
                    index = int(index_ctx.getText())

                    id_index = index_id_ctx.getText()
                    if id_index in duplicates:
                        raise Exception('The register index is duplicated')
                    else:
                        duplicates.add(id_index)
                    
                    if index < 0 or index >= len(qubits):
                        raise Exception('The register index is out of range')
                    gate_qargs.append(qubits[index])
                else:
                    gate_qargs.extend(qubits)

            cindex_id_list_ctx = ctx.indexIdentifierList()
            cindex_id_list = cindex_id_list_ctx.indexIdentifier()
            for index_id_ctx in cindex_id_list:
                id = index_id_ctx.Identifier().getText()
                if not id in self.cregister_table:
                    raise Exception('Unknown classical register')

                clbits = self.cregister_table[id]
                exp_list_ctx = index_id_ctx.expressionList()
                if exp_list_ctx != None:
                    exp_list = exp_list_ctx.expression()
                    if len(exp_list) > 1:
                        raise Exception('Illegal register index')

                    index_ctx = exp_list[0].expressionTerminator()
                    index = int(index_ctx.getText())

                    id_index = index_id_ctx.getText()
                    if id_index in duplicates:
                        raise Exception('The register index is duplicated')
                    else:
                        duplicates.add(id_index)
                    
                    if index < 0 or index >= len(clbits):
                        raise Exception('The register index is out of range')
                    gate_cargs.append(clbits[index])
                else:
                    gate_cargs.extend(clbits)
            
            if len(gate_qargs) != len(gate_cargs):
                raise Exception('The number of qubits does not match the number of classical bits.')
            self.ir.add_op_node(MEASURE.label, [], gate_qargs, gate_cargs)
        except Exception as e:
            traceback.print_exc()
            self.errors.append(ctx.start.line)
    
    def enterBranchingStatement(self, ctx: Qasm2Parser.BranchingStatementContext):
        self.branching = True

    def exitBranchingStatement(self, ctx: Qasm2Parser.BranchingStatementContext):
        try:   
            expCtx = ctx.expression()
            logicalAndCtx = expCtx.logicalAndExpression()
            bitOrCtx = logicalAndCtx.bitOrExpression()
            xOrCtx = bitOrCtx.xOrExpression()
            bitAndCtx = xOrCtx.bitAndExpression()
            eqCtx = bitAndCtx.equalityExpression()

            eqOpCtx = eqCtx.equalityOperator()
            if eqOpCtx != None:
                relation = eqOpCtx.getText()
                val = int(eqCtx.comparisonExpression().getText())
                clCtx = eqCtx.equalityExpression()
            else:
                cmpCtx = eqCtx.comparisonExpression()
                relation = cmpCtx.comparisonOperator().getText()
                val = int(cmpCtx.bitShiftExpression().getText())
                clCtx = cmpCtx

            cmexpCtx = clCtx.comparisonExpression()
            bsexpCtx = cmexpCtx.bitShiftExpression()
            adexpCtx = bsexpCtx.additiveExpression()
            muexpCtx = adexpCtx.multiplicativeExpression()
            termCtx = muexpCtx.expressionTerminator()

            idxExpCtx = termCtx.expression()
            if idxExpCtx != None:
                nameExpCtx = termCtx.expressionTerminator()
                idx = int(idxExpCtx)
                clbits = [self.cregister_table[nameExpCtx.getText()][idx]]
            else:
                clbits = self.cregister_table[termCtx.getText()]

            for v in self.conditional_gates:
                self.ir.add_node_condition(v, clbits, relation, val)
        except Exception as e:
            traceback.print_exc()
            self.errors.append(ctx.start.line)

        self.branching = False

    def exitQuantumBarrier(self, ctx:Qasm2Parser.QuantumBarrierContext):
        duplicates = set()
        
        try:
            id_list_ctx = ctx.indexIdentifierList()
            id_list = id_list_ctx.indexIdentifier()
                
            for index_id_ctx in id_list:
                id = index_id_ctx.Identifier().getText()
                if not id in self.qregister_table:
                    raise Exception('Unknown qubit register')

                qubits = self.qregister_table[id]
                exp_list_ctx = index_id_ctx.expressionList()
                if exp_list_ctx != None:
                    exp_list = exp_list_ctx.expression()
                    if len(exp_list) > 1:
                        raise Exception('Illegal register index')

                    index_ctx = exp_list[0].expressionTerminator()
                    index = int(index_ctx.getText())

                    id_index = index_id_ctx.getText()
                    if id_index in duplicates:
                        raise Exception('The register index is duplicated')
                    else:
                        duplicates.add(id_index)
                    
                    if index < 0 or index >= len(qubits):
                        raise Exception('The register index is out of range')
        except Exception as e:
            traceback.print_exc()
            self.errors.append(ctx.start.line)