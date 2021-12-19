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

#ifndef _CONDITION_H_
#define _CONDITION_H_

#include <vector>
#include <functional>
using namespace std;

enum RELATION {
    EQ,
    NE,
    LT,
    GT,
    LE,
    GE
};

class condition {
public:
    condition();
    condition(const vector<size_t>& clbits, RELATION sym, int val);
    bool isValid() const;
    bool operator==(const condition & c) const;

    vector<size_t> m_clbits;
    RELATION m_symbol;
    int m_value;    
};

struct hash_condition{
    size_t operator()(const condition & c) const {
        size_t code = hash<int>()(c.m_value);
        for (auto it = c.m_clbits.begin(); it != c.m_clbits.end(); ++it) {
            code ^= hash<size_t>()(*it);
        }
        return code;
    }
};

#endif