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

#include "SpinQuasar.h"

bool  SpinQuasar::running = true;
vector<double> SpinQuasar::probabilities;

void SpinQuasar::init(const string& ip) {
    set_on_closed_callback(SpinQuasar::on_close);
    set_on_failed_callback(SpinQuasar::on_failed);
    set_on_opened_callback(SpinQuasar::on_opened);
    set_login_response_callback(SpinQuasar::on_login_response);
    set_push_task_response_callback(SpinQuasar::on_push_task_response);
    set_task_finished_post_callback(SpinQuasar::on_task_finished_post_callback);
    
    connect_to_server(ip.c_str(), 55444);
    this_thread::sleep_for(chrono::seconds(1));
}

vector<double> SpinQuasar::triangulum_run(const string& task_name, const string& task_desc, const string& circuit, int qnum) {
    push_task_request(task_name.c_str(), task_desc.c_str(), circuit.c_str(), qnum);
    while(running) {
        this_thread::sleep_for(chrono::seconds(1));
    }
    if (qnum == 1) {
        double zero = 0.0;
        double one = 0.0;
        for (size_t i=0; i<probabilities.size()/2; i++)
            zero += probabilities[i];
        for (size_t j=probabilities.size()/2; j<probabilities.size(); j++)
            zero += probabilities[j];
        probabilities.clear();
        probabilities.push_back(zero);
        probabilities.push_back(one);
    } else if (qnum == 2) {
        double zero = probabilities[0] + probabilities[1];
        double one = probabilities[2] + probabilities[3];
        double second = probabilities[4] + probabilities[5];
        double third = probabilities[6] + probabilities[7];
        probabilities.clear();
        probabilities.push_back(zero);
        probabilities.push_back(one);
        probabilities.push_back(second);
        probabilities.push_back(third);
    } 
    return probabilities;
}

void SpinQuasar::on_opened()
{
    std::cout << "Connect to server successfully!" << std::endl;
    if (request_login("user9", "123456") != 0) {
        std::cout << __FUNCTION__ << "Send request-login message failed!" << std::endl;
    }
}

void SpinQuasar::on_close()
{
    std::cout << "The connection has been closed!" << std::endl;
}

void SpinQuasar::on_failed()
{
    std::cout << "Connect to server failed!" << std::endl;
}

void SpinQuasar::on_login_response(const char *msg)
{
    std::cout << __FUNCTION__ << std::endl;
    std::cout << msg << std::endl;
}

void SpinQuasar::on_push_task_response(const char *msg)
{
    std::cout << __FUNCTION__ << std::endl;
    std::cout << msg << std::endl;
}

void SpinQuasar::on_task_finished_post_callback(const char *msg)
{
    std::cout << __FUNCTION__ << std::endl;
    std::cout << msg << std::endl;

    string result_msg(msg);
    size_t keypos = result_msg.find("execution");
    if (keypos == std::string::npos) {
        cerr << "Illegal task result message." << endl;
        throw std::exception();
    }
    size_t pos = keypos + 9;
    size_t start = result_msg.find('[', pos);
    if (start == std::string::npos) {
        cerr << "Illegal task result message." << endl;
        throw std::exception();
    }
    size_t end = result_msg.find(']', start+1);
    if (end == std::string::npos) {
        cerr << "Illegal task result message." << endl;
        throw std::exception();
    }
    string arr = result_msg.substr(start+1, end-start-1);

    istringstream iss(arr);
    string token;
    while (getline(iss, token, ',')) {
        probabilities.push_back(stod(token));
    }

    SpinQuasar::running = false;
}