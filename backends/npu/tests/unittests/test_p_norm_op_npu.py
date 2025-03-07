#  Copyright (c) 2022 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import numpy as np

import paddle
from tests.op_test import OpTest

paddle.enable_static()


def p_norm(x, axis, porder, keepdims=False, reduce_all=False):
    r = []
    if axis is None or reduce_all:
        x = x.flatten()
        if porder == np.inf:
            r = np.amax(np.abs(x), keepdims=keepdims)
        elif porder == -np.inf:
            r = np.amin(np.abs(x), keepdims=keepdims)
        else:
            r = np.linalg.norm(x, ord=porder, keepdims=keepdims)
    elif isinstance(axis, list or tuple) and len(axis) == 2:
        if porder == np.inf:
            axis = tuple(axis)
            r = np.amax(np.abs(x), axis=axis, keepdims=keepdims)
        elif porder == -np.inf:
            axis = tuple(axis)
            r = np.amin(np.abs(x), axis=axis, keepdims=keepdims)
        elif porder == 0:
            axis = tuple(axis)
            r = x.astype(bool)
            r = np.sum(r, axis, keepdims=keepdims)
        elif porder == 1:
            axis = tuple(axis)
            r = np.sum(np.abs(x), axis, keepdims=keepdims)
        else:
            axis = tuple(axis)
            xp = np.power(np.abs(x), porder)
            s = np.sum(xp, axis=axis, keepdims=keepdims)
            r = np.power(s, 1.0 / porder)
    else:
        if isinstance(axis, list):
            axis = tuple(axis)
        r = np.linalg.norm(x, ord=porder, axis=axis, keepdims=keepdims)
    r = r.astype(x.dtype)

    return r


class TestPnormOp(OpTest):
    def set_npu(self):
        self.__class__.use_custom_device = True

    def setUp(self):
        self.set_npu()
        self.op_type = "p_norm"
        self.init_test_case()
        x = (np.random.random(self.shape) + 0.5).astype(self.dtype)
        norm = p_norm(x, self.axis, self.porder, self.keepdim)
        self.inputs = {'X': x}
        self.attrs = {
            'epsilon': self.epsilon,
            'axis': self.axis,
            'keepdim': self.keepdim,
            'porder': float(self.porder)
        }
        self.outputs = {'Out': norm}
        self.gradient = self.calc_gradient()

    def test_check_output(self):
        if self.dtype == "float16":
            self.check_output_with_place(
                paddle.CustomPlace('ascend', 0), atol=5e-3)
        else:
            self.check_output_with_place(paddle.CustomPlace('ascend', 0))

    def test_check_grad(self):
        self.check_grad_with_place(
            paddle.CustomPlace('ascend', 0), ['X'],
            'Out',
            user_defined_grads=self.gradient)

    def init_test_case(self):
        self.shape = [2, 3, 4, 5]
        self.axis = 1
        self.epsilon = 1e-12
        self.porder = 2.0
        self.keepdim = False
        self.init_dtype()

    def init_dtype(self):
        self.dtype = "float32"

    def calc_gradient(self):
        self.attrs = {
            'epsilon': self.epsilon,
            'axis': self.axis,
            'keepdim': self.keepdim,
            'porder': float(self.porder)
        }
        x = self.inputs["X"]
        porder = self.attrs["porder"]
        axis = self.attrs["axis"]
        if porder == 0:
            grad = np.zeros(x.shape).astype(x.dtype)
        elif porder in [float("inf"), float("-inf")]:
            norm = p_norm(x, axis=axis, porder=porder, keepdims=True)
            x_abs = np.abs(x)
            grad = np.sign(x)
            grad[x_abs != norm] = 0.0
        else:
            norm = p_norm(x, axis=axis, porder=porder, keepdims=True)
            grad = np.power(norm, 1 - porder) * np.power(
                np.abs(x), porder - 1) * np.sign(x)

        numel = 1
        for s in x.shape:
            numel *= s
        numel /= x.shape[axis]
        return [grad.astype(x.dtype) * 1 / numel]


class TestPnormOp2(TestPnormOp):
    def init_test_case(self):
        self.shape = [3, 20, 3]
        self.axis = 2
        self.epsilon = 1e-12
        self.porder = 2.0
        self.keepdim = True
        self.init_dtype()


class TestPnormOp3(TestPnormOp):
    def init_test_case(self):
        self.shape = [3, 20, 3]
        self.axis = 2
        self.epsilon = 1e-12
        self.porder = np.inf
        self.keepdim = True
        self.init_dtype()


class TestPnormOp4(TestPnormOp3):
    def init_test_case(self):
        self.shape = [3, 20, 3]
        self.axis = 2
        self.epsilon = 1e-12
        self.porder = -np.inf
        self.keepdim = True
        self.init_dtype()


class TestPnormOp5(TestPnormOp3):
    def init_test_case(self):
        self.shape = [3, 20, 3]
        self.axis = 2
        self.epsilon = 1e-12
        self.porder = 0
        self.keepdim = True
        self.init_dtype()


class TestPnormOp6(TestPnormOp3):
    def init_test_case(self):
        self.shape = [2, 3, 4, 5]
        self.axis = 1
        self.epsilon = 1e-12
        self.porder = 0.5
        self.keepdim = False
        self.init_dtype()


class TestPnormOpfp16(TestPnormOp):
    def init_dtype(self):
        self.dtype = "float16"


class TestPnormOp2fp16(TestPnormOp2):
    def init_dtype(self):
        self.dtype = "float16"


class TestPnormOp3fp16(TestPnormOp3):
    def init_dtype(self):
        self.dtype = "float16"


class TestPnormOp4fp16(TestPnormOp4):
    def init_dtype(self):
        self.dtype = "float16"


class TestPnormOp5fp16(TestPnormOp5):
    def init_dtype(self):
        self.dtype = "float16"


if __name__ == "__main__":
    unittest.main()
