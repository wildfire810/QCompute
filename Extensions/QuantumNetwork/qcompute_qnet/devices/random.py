#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Baidu, Inc. All Rights Reserved.
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

r"""
Module for random number generators.
"""

import math
from enum import Enum
from typing import List, Optional
from qcompute_qnet.core.des import Entity
from qcompute_qnet.quantum.circuit import Circuit

__all__ = [
    "RandomNumberGenerator"
]


class RandomNumberGenerator(Entity):
    r"""Class for creating a random number generator.

    The random numbers are generated by running a quantum circuit.

    Important:
        We can switch the ``backend`` to get random numbers from real quantum devices,
        for example, using the QCompute backend ``CloudIoPCAS``.
    """

    def __init__(self, name, env: Optional["DESEnv"] = None):
        r"""Constructor for RandomNumberGenerator class.

        Args:
            name (str): name of the random number generator
            env (DESEnv, optional): discrete-event simulation environment
        """
        super().__init__(name, env)

    def init(self) -> None:
        r"""Random number generator initialization.
        """
        assert self.owner != self, f"The random number generator {self.name} has no owner!"

    @staticmethod
    def random(length: int, backend: Optional[Enum] = None, prob=None) -> List[int]:
        r"""Generate random bits by running a quantum circuit.

        Warning:
            The random bits are generated by preparing a zero state and then performing a Ry gate followed by
            measurement in computational basis. This is just one particular option for random bits' generation with
            given bias and more serious post-processing steps are omitted in this version.
            Also note that we have to run the circuit shot by shot because most backends
            only support to return the collected probability distribution instead of the primitive measurement data.

        Important:
            QCompute provides a more efficient interface for obtaining random bits from real quantum devices.
            Please refer to its latest API documentation for details.

        Args:
            length (int): the number of random bits
            prob (List[float]): probability distribution of random bits
            backend (Enum, optional): backend of the quantum circuit

        Returns:
            List[int]: generated random numbers
        """
        assert prob is None or isinstance(prob, List), "`prob` should be a list."
        assert sum(prob) == 1, "Invalid `prob` input. The sum of `prob` is not equal to one!"
        prob = [0.5, 0.5] if prob is None else prob
        cir = Circuit()
        theta = 2 * math.acos(math.sqrt(prob[0]))
        cir.ry(0, theta)
        cir.measure()
        results = []
        for _ in range(length):
            result = cir.run(shots=1, backend=backend)
            results.append(int(list(result['counts'].keys())[0]))
        return results