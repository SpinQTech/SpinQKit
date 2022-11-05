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
from spinqkit import Circuit, get_compiler, get_basic_simulator, BasicSimulatorConfig
from spinqkit import Rz, Ry, CX, Z
from spinqkit.primitive import calculate_pauli_expectation, generate_vector_encoding
import numpy as np
import torch
from torch import nn
import torch.optim as optim
from torch.autograd import Variable, Function

class VariationalClassifier():
    def __init__(self, layer_num, qubit_num, backend, config):
        self.__backend = backend
        self.__config = config
        self.__compiler = get_compiler("native")
        self.__layer_num = layer_num
        self.__qubit_num = qubit_num

    def build_circuit(self, weights, X):
        circ = Circuit()
        q = circ.allocateQubits(self.__qubit_num)
        
        prep_list = generate_vector_encoding(X.detach().numpy(), q)
        circ.extend(prep_list)
        
        for i in range(self.__layer_num):
            circ << (Rz, q[0], weights[i * self.__layer_num + 0].item())
            circ << (Ry, q[0], weights[i * self.__layer_num + 1].item())
            circ << (Rz, q[0], weights[i * self.__layer_num + 2].item())
            circ << (Rz, q[1], weights[i * self.__layer_num + 3].item())
            circ << (Ry, q[1], weights[i * self.__layer_num + 4].item())
            circ << (Rz, q[1], weights[i * self.__layer_num + 5].item())
            circ << (CX, q)
        # Pauli Measurement
        circ << (Z, q[0])
        return circ

    def run(self, weights, bias, features):
        expectations = []
        for X in features:
            circ = self.build_circuit(weights, X)
            optimization_level = 0
            exe = self.__compiler.compile(circ, optimization_level)
            result = self.__backend.execute(exe, self.__config)
            expectations.append(calculate_pauli_expectation('Z', result.probabilities) + bias)
        return expectations

class QuantumFunction(Function):
    @staticmethod
    def forward(ctx, weights, bias, features, quantum_classifier, shift):
        ctx.quantum_classifier = quantum_classifier
        ctx.shift = shift
        expectations = quantum_classifier.run(weights, bias, features)
        result = torch.tensor(expectations)
        ctx.save_for_backward(weights, bias, features)
        return result

    @staticmethod
    def backward(ctx, grad_output):
        weights, bias, features = ctx.saved_tensors 
      
        gradients = []
        for i in range(len(weights)):
            elem = weights[i]
            weights[i] = elem + ctx.shift
            expectation_right = torch.tensor(ctx.quantum_classifier.run(weights, bias, features))
            weights[i] = elem - ctx.shift
            expectation_left = torch.tensor(ctx.quantum_classifier.run(weights, bias, features))
            gradient = (expectation_right - expectation_left)/2

            gradients.append(gradient)
            weights[i] = elem       
        gradients = torch.cat(gradients, dim=0).reshape(len(weights), len(features))
        gradients = gradients.t()
        
        g_w = torch.matmul(grad_output.float(), gradients.float())
        g_b = torch.matmul(grad_output.float(), torch.ones((len(features), 1)))

        return g_w, g_b, None, None, None

class QuantumModel(nn.Module):
    def __init__(self, qubit_num, layer_num, shift, backend, config):
        super().__init__()
        self.__shift = shift
        self.__quantum_classifier = VariationalClassifier(layer_num, qubit_num, backend, config)

        init_w = 0.01 * torch.randn(layer_num * qubit_num * 3, requires_grad = True)    
        init_b = torch.tensor(0.0, requires_grad = True)

        self.w = nn.Parameter(init_w)
        self.b = nn.Parameter(init_b)

    def forward(self, features):
        return QuantumFunction.apply(self.w, self.b, features, self.__quantum_classifier, self.__shift)


# Prepare the data
data = np.loadtxt("resource/iris_classes_data.txt")
Xdata = data[:, 0:2]
padding = 0.3 * np.ones((len(Xdata), 1))
X_pad = np.c_[np.c_[Xdata, padding], np.zeros((len(Xdata), 1))]
normalization = np.sqrt(np.sum(X_pad ** 2, -1))
features = (X_pad.T / normalization).T

Y = data[:, -1]
np.random.seed(0)
num_data = len(Y)
num_train = int(0.75 * num_data)
index = np.random.permutation(range(num_data))
features_train = Variable(torch.tensor(features[index[:num_train]]).float(), requires_grad = False)
labels_train = Variable(torch.tensor(Y[index[:num_train]]).float(), requires_grad = False)
features_val = Variable(torch.tensor(features[index[num_train:]]))
labels_val = Y[index[num_train:]]

# Set up the backend
engine = get_basic_simulator()
config = BasicSimulatorConfig()
config.configure_shots(1024)
config.configure_measure_qubits([0])

# Set up the model and the optimizer
model = QuantumModel(2, 6, np.pi/2, engine, config)
optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.9, nesterov=True)
loss_fn = nn.MSELoss()
iter = 45
batch_size = 5

# Optimize
for i in range(iter):
    batch_index = np.random.randint(0, num_train, (batch_size,))
    feats_train_batch = features_train[batch_index]
    Y_train_batch = labels_train[batch_index]

    optimizer.zero_grad()
    pred = model(feats_train_batch)
    
    loss = loss_fn(pred, Y_train_batch)
    print("The loss value is ", loss.item())
    loss.backward()
    optimizer.step()

# Validate
total_error = 0
for k in range(len(features_val)):
    pred = model(features_val[k].unsqueeze(0))
    if abs(labels_val[k] - np.sign(pred.item())) > 1e-5:
        total_error = total_error + 1

print("The number of wrong predictions is ", total_error)
