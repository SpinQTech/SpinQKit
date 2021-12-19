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

#ifndef _GATE_ATTR_H_
#define _GATE_ATTR_H_

#include <iostream>
#include <complex>
#include <string>
#include "matrix.h"
#include "simple_json.h"

#define SQRT2          1.4142135624
#ifndef PI
#define PI             3.1415926532
#endif
#define INVALID_QUBIT  0xFFFF

using namespace std;

typedef complex<double> StateType;

class gateAttr {
private:
    double             m_angle;

public:
    gateAttr();
    gateAttr(double angle);

    ~gateAttr();

    bool setAngle(double angle);

    double getAngle() const;
    matrix<StateType> getGateXMatrix() const;
    matrix<StateType> getGateYMatrix() const;
    matrix<StateType> getGateZMatrix() const;
    matrix<StateType> getGatePMatrix() const;
};


#endif // _GATE_ATTR_
