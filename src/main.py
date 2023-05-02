#  Copyright 2021 Hugging Face Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from omegaconf import OmegaConf
from logging import getLogger
from typing import Type

import hydra
from hydra.core.config_store import ConfigStore
from hydra.utils import get_class

from backends.base import Backend
from backends.pytorch import PyTorchConfig
from backends.onnxruntime import ORTConfig
from benchmark.config import BenchmarkConfig

# Register resolvers
OmegaConf.register_new_resolver("pytorch_version", PyTorchConfig.version)
OmegaConf.register_new_resolver("onnxruntime_version", ORTConfig.version)

# Register configurations
cs = ConfigStore.instance()
cs.store(name="base_benchmark", node=BenchmarkConfig)
cs.store(group="backends", name="pytorch_backend", node=PyTorchConfig)
cs.store(group="backends", name="onnxruntime_backend", node=ORTConfig)

LOGGER = getLogger("benchmark")


@hydra.main(config_path="../configs", config_name="benchmark", version_base=None)
def run(config: BenchmarkConfig) -> None:
    # Allocate requested target backend
    backend_factory: Type[Backend] = get_class(config.backend._target_)
    backend: Backend = backend_factory.allocate(config)

    # Run benchmark and reference
    benchmark, _ = backend.execute(config)

    # Save the resolved config
    OmegaConf.save(config, ".hydra/config.yaml", resolve=True)

    benchmark.perfs.to_csv("perfs.csv", index_label="id")
    benchmark.details.to_csv("details.csv", index_label="id")

if __name__ == '__main__':
    run()