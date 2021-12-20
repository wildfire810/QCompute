#!/usr/bin/python3
# -*- coding: utf8 -*-

# Copyright (c) 2020 Baidu, Inc. All Rights Reserved.
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

"""
This is a simple case of using Hadamard gate and CNOT gate.
Results will be fetched from a cloud program.
"""

from pprint import pprint
import sys

sys.path.append('../..')  # "from QCompute import *" requires this
from QCompute import *

matchSdkVersion('Python 2.0.3')

# Your token:
# Define.hubToken = ''

# Create environment
env = QEnv()
# Choose backend Baidu Cloud Quantum Simulator-Sim2 Water
env.backend(BackendName.CloudBaiduSim2Water)

# Initialize the two-qubit circuit
q = env.Q.createList(2)

# We apply an X gate on the 0th qubit firstly.
# Also, you can comment it as you like.
X(q[0])

# Then we apply a Hadamard gate on the 0th qubit,
# where we comment the gate in order to hint the user you to try yourself.
# H(q[0])

# We need a CX gate to generate an entangle quantum state
CX(q[0], q[1])

# Measure with the computational basis
MeasureZ(*env.Q.toListPair())

# Commit the request with 1024 shots to the cloud
taskResult = env.commit(1024, fetchMeasure=True)

pprint(taskResult)