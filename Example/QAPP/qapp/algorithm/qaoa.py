# -*- coding: UTF-8 -*-
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

"""
Quantum Approximate Optimization Algorithm
"""

from typing import List, Union
import numpy as np
from QCompute.QPlatform.QEnv import QEnv
from QCompute.QPlatform.QOperation.Measure import MeasureZ
from qapp.circuit import QAOAAnsatz
from qapp.circuit import PauliMeasurementCircuit
from qapp.circuit import PauliMeasurementCircuitWithAncilla
from qapp.circuit import SimultaneousPauliMeasurementCircuit
from qapp.optimizer import BasicOptimizer


class QAOA:
    """
    Quantum Approximate Optimization Algorithm class
    """
    def __init__(self, num: int, hamiltonian: List, ansatz: QAOAAnsatz, optimizer: BasicOptimizer,
                 backend: str, measurement: str = 'default', delta: float = 0.1):
        """The constructor of the QAOA class

        :param num: Number of qubits
        :param hamiltonian: Hamiltonian used to construct the QAOA ansatz
        :param ansatz: QAOA ansatz used to search for the maximum eigenstate of the Hamiltonian
        :param optimizer: Optimizer used to optimize the parameters in the ansatz
        :param backend: Backend to be used in this task. Please refer to https://quantum-hub.baidu.com/quickGuide for details
        :param measurement: Method chosen from 'default', 'ancilla', and 'SimMeasure' for measuring the expectation value, defaults to 'default'
        :param delta: Parameter used to calculate gradients, defaults to 0.1
        """
        self._num = num
        self._hamiltonian = hamiltonian
        self._ansatz = ansatz
        self._optimizer = optimizer
        self._backend = backend
        self._measurement = measurement
        self._delta = delta
        if measurement == 'default':
            self._measurement_circuit = PauliMeasurementCircuit
        elif measurement == 'ancilla':
            self._measurement_circuit = PauliMeasurementCircuitWithAncilla
        elif measurement == 'SimMeasure':
            self._measurement_circuit = SimultaneousPauliMeasurementCircuit
        else:
            raise ValueError('Invalid measurement method!')
        self._maximum_eigenvalue = "Run QAOA.run() first"

    def _pauli_expectation(self, shots: int) -> float:
        """Returns the expectation value of the Hamiltonian

        :param shots: Number of measurement shots
        :return: Expectation value of the Hamiltonian
        """
        measurement_circuit = self._measurement_circuit(self._num, self._hamiltonian)
        expectation = measurement_circuit.get_expectation([self._ansatz], shots, self._backend)

        return expectation

    def get_measure(self, shots: int = 1024) -> dict:
        """Returns the measurement results

        :param shots: Number of measurement shots, defaults to 1024
        :return: Measurement results in bitstrings with the number of counts
        """
        env = QEnv()
        env.backend(self._backend)
        q = env.Q.createList(self._num)
        # Add circuit
        self._ansatz.add_circuit(q)
        # Measurement
        MeasureZ(q, range(self._num))
        counts = env.commit(shots, fetchMeasure=True)['counts']

        return counts

    def _compute_gradient(self, parameters: np.ndarray, shots: int) -> np.ndarray:
        """Computes gradient by the finite-difference method

        :param parameters: Current parameters of the ansatz
        :param shots: Number of measurement shots
        """
        gradient = np.zeros_like(parameters)
        for i in range(len(parameters)):
            param_plus = parameters.copy()
            param_minus = parameters.copy()
            param_plus[i] += self._delta / 2
            param_minus[i] -= self._delta / 2
            loss_plus = self._compute_loss(param_plus, shots)
            loss_minus = self._compute_loss(param_minus, shots)
            gradient[i] = ((loss_plus - loss_minus) / self._delta)
        self._ansatz.set_parameters(parameters)

        return gradient

    def _compute_loss(self, parameters: np.ndarray, shots: int) -> float:
        """Computes loss

        :param parameters: Current parameters of the ansatz
        :param shots: Number of measurement shots
        """
        self._ansatz.set_parameters(parameters)
        loss = -self._pauli_expectation(shots=shots)

        return loss

    def get_gradient(self, shots: int = 1024) -> np.ndarray:
        """Calculates the gradient with respect to current parameters in circuit

        :param shots: Number of measurement shots, defaults to 1024
        :return: Gradient with respect to current parameters
        """
        curr_param = self._ansatz.parameters
        gradient = self._compute_gradient(curr_param, shots)

        return gradient

    def get_loss(self, shots: int = 1024) -> float:
        """Calculates the loss with respect to current parameters in circuit

        :param shots: Number of measurement shots, defaults to 1024
        :return: Loss with respect to current parameters
        """
        loss = -self._pauli_expectation(shots=shots)

        return loss

    def run(self, shots: int = 1024):
        """Searches for the maximum eigenvalue of the input Hamiltonian with the given ansatz and optimizer

        :param shots: Number of measurement shots, defaults to 1024
        """
        self._optimizer.minimize(shots, self._compute_loss, self._compute_gradient)
        self._maximum_eigenvalue = -self._optimizer._loss_history[-1]

    @property
    def maximum_eigenvalue(self) -> Union[str, float]:
        """The optimized maximum eigenvalue from last run

        :return: Optimized maximum eigenvalue from last run
        """

        return self._maximum_eigenvalue

    def set_backend(self, backend: str):
        """Sets the backend to be used

        :param backend: Backend to be used
        """
        self._backend = backend
