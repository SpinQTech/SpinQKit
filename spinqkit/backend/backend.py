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

from .basic_simulator_backend import BasicSimulatorBackend
from .triangulum_backend import TriangulumBackend
from .spinq_cloud_backend import SpinQCloudBackend

BS = BasicSimulatorBackend()
TB = TriangulumBackend()

def get_basic_simulator():
    return BS

def get_triangulum():
    return TB

def get_spinq_cloud(username, signStr):
    return SpinQCloudBackend(username, signStr)