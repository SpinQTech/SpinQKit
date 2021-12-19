/**
 * Copyright 2021 SpinQ Technology Co., Ltd.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef _STATE_MANAGER_H_
#define _STATE_MANAGER_H_

#include "../utilities/circuit.h"
#include "../utilities/condition.h"
#include "quantum_state.h"

#include <vector>
#include <unordered_set>
#include <unordered_map>
#include <iostream>
using namespace std;

class state_manager {
public:
    void execute(const circuit & circ);
    vector<StateType> getStateVector();
    vector<double> getProbabilities();
private:
    size_t m_qubit_num;
    size_t m_clbit_num;
    vector<quantum_state> m_states;
    unordered_set<size_t> m_measured_qubits;
    unordered_map<condition, vector<size_t>, hash_condition> m_cond_state;
    unordered_map<size_t, condition> m_secondary_index; // clbit to condition
    
    bool check_qubits(const vector<gate_unit>::iterator & git);
    void invalidate_condition_entry(size_t clbit);
};

#endif