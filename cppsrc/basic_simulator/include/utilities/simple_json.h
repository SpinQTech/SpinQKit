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

#ifndef _SIMPLE_JSON_H_
#define _SIMPLE_JSON_H_

#include <vector>
#include <string>

#define INVALID_INT  0xFFFFFFFF
#define INVALID_DOUBLE 0xFFFFFFFF

class simple_json {
private:
    std::string   m_json;

private:
    std::vector<size_t> getPairPosition( const std::string & json
                                       , char c1, char c2, size_t pos);

public:
    simple_json(const std::string & str_json);

    std::string getSubJSON(char c1, char c2, uint8_t start_pos);
    std::string getString(const std::string & key);
    int getInteger(const std::string & key);
    double getDouble(const std::string & key);
    std::vector<std::string> getJSONArray(const std::string & key);
};

#endif // _SIMPLE_JSON_H_
