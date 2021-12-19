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

from spinqkit import get_triangulum, get_compiler, Circuit, TriangulumConfig
from spinqkit import H, CX

engine = get_triangulum()
comp = get_compiler("native")

circ = Circuit()
q = circ.allocateQubits(2)
circ << (H, q[0])
circ << (CX, (q[0], q[1]))


exe = comp.compile(circ, 0)
config = TriangulumConfig()
config.configure_ip("192.168.1.186")
config.configure_task("task1", "")

result = engine.execute(exe, config)
print(result.probabilities)
