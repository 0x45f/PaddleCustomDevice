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
void TrilTriuKernel(const Context& dev_ctx,
                    const phi::DenseTensor& x,
                    int diagonal,
                    bool lower,
                    phi::DenseTensor* out) {
  const auto* x_data = x.data<T>();
  auto* out_data = dev_ctx.template Alloc<T>(out);

  const auto& dims = x.dims();
  const auto H = dims[dims.size() - 2];
  const auto W = dims[dims.size() - 1];

  std::string op_type = lower ? "Tril" : "Triu";
  NPUAttributeMap attr_input = {{"diagonal", diagonal}};

  auto op_func_tril = [](const std::vector<phi::DenseTensor>& inputs,
                         const std::vector<phi::DenseTensor>& outputs,
                         const NPUAttributeMap& attrs,
                         const Context& dev_ctx) {
    const auto& runner = NpuOpRunner("Tril", inputs, outputs, attrs);
    runner.Run(dev_ctx.stream());
  };

  auto op_func_triu = [](const std::vector<phi::DenseTensor>& inputs,
                         const std::vector<phi::DenseTensor>& outputs,
                         const NPUAttributeMap& attrs,
                         const Context& dev_ctx) {
    const auto& runner = NpuOpRunner("Triu", inputs, outputs, attrs);
    runner.Run(dev_ctx.stream());
  };
  if (x.dtype() == phi::DenseTensorMeta::DataType::BOOL) {
    if (lower) {
      NpuOpRunner::TypeAdapter({x},
                               {*out},
                               attr_input,
                               dev_ctx,
                               op_func_tril,
                               {phi::DenseTensorMeta::DataType::UINT8},
                               {phi::DenseTensorMeta::DataType::UINT8});
    } else {
      NpuOpRunner::TypeAdapter({x},
                               {*out},
                               attr_input,
                               dev_ctx,
                               op_func_triu,
                               {phi::DenseTensorMeta::DataType::UINT8},
                               {phi::DenseTensorMeta::DataType::UINT8});
    }
  } else {
    const auto& runner = NpuOpRunner(op_type, {x}, {*out}, attr_input);
    runner.Run(dev_ctx.stream());
  }
}

// template <typename T, typename Context>
// DenseTensor TrilTriu(const Context& ctx,
//                      const phi::DenseTensor& x,
//                      int diagonal,
//                      bool lower) {
//     phi::DenseTensor dense_out;
//     phi::MetaTensor meta_out(&dense_out);
//     phi::TrilTriuInferMeta(x, diagonal, lower, &meta_out);
//     TrilTriuKernel<T, Context>(ctx, x, diagonal, lower, &dense_out);
//     return dense_out;
// }

}  // namespace custom_kernel

PD_REGISTER_PLUGIN_KERNEL(tril_triu,
                          ascend,
                          ALL_LAYOUT,
                          custom_kernel::TrilTriuKernel,
                          bool,
                          float,
                          int,
                          phi::dtype::float16) {}
