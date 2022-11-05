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
from typing import Callable, Tuple
import numpy as np
from .optimizer import Optimizer


class ADAM(Optimizer):
    def __init__(self, maxiter: int = 1000, tolerance: float = 1e-6, learning_rate: float = 0.01, beta1: float = 0.9,
                 beta2: float = 0.99, noise_factor: float = 1e-8, verbose: bool = False):

        super().__init__()
        self.__maxiter = maxiter
        self.__tolerance = tolerance
        self.__learning_rate = learning_rate
        self.__beta1 = beta1
        self.__beta2 = beta2
        self.__noise_factor = noise_factor
        self.__verbose = verbose

    def optimize(self, obj_func: Callable, init_point: np.ndarray, grad_func: Callable, *args: Tuple):
        derivative = grad_func(init_point, *args)
        step = 0
        mt = np.zeros(np.shape(derivative))
        vt = np.zeros(np.shape(derivative))

        params = init_point
        while step < self.__maxiter:
            if step > 0:
                derivative = grad_func(params, *args)
            mt = self.__beta1 * mt + (1 - self.__beta1) * derivative
            vt = self.__beta2 * vt + (1 - self.__beta2) * derivative * derivative
            step += 1
            rate_eff = self.__learning_rate * np.sqrt(1 - self.__beta2 ** step) / (1 - self.__beta1 ** step)

            params_new = params - rate_eff * mt / (np.sqrt(vt) + self.__noise_factor)

            if self.__verbose:
                print(params_new)
                print(obj_func(params_new, *args))

            if np.linalg.norm(params - params_new) < self.__tolerance:
                params = params_new
                break
            else:
                params = params_new

        return params, obj_func(params, *args)
