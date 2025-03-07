// Copyright (c) 2022 PaddlePaddle Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "kernels/funcs/npu_funcs.h"
#include "kernels/funcs/npu_op_runner.h"

namespace custom_kernel {

template <typename T, typename Context>
void IncrementKernel(const Context& dev_ctx,
                     const phi::DenseTensor& x,
                     float step,
                     phi::DenseTensor* out) {
  dev_ctx.template Alloc<T>(out);

  phi::DenseTensor step_tensor;
  phi::DenseTensorMeta meta = {x.dtype(), {1}};
  step_tensor.set_meta(meta);
  dev_ctx.template Alloc<T>(&step_tensor);

  FillNpuTensorWithConstant<T>(&step_tensor, dev_ctx, static_cast<T>(step));

  const auto& runner = NpuOpRunner("Add", {x, step_tensor}, {*out}, {});

  auto stream = dev_ctx.stream();
  runner.Run(stream);
}

}  // namespace custom_kernel

PD_REGISTER_PLUGIN_KERNEL(increment,
                          ascend,
                          ALL_LAYOUT,
                          custom_kernel::IncrementKernel,
                          int,
                          int64_t,
                          float,
                          double,
                          phi::dtype::float16) {}
