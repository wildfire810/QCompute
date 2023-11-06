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
An example of MBQC cluster-state circuit of size (w, d).
"""

import numpy
from functools import reduce
from Extensions.QuantumNetwork.qcompute_qnet.quantum.circuit import Circuit

# Set the size of the cluster state
# Number of rows
w = 3
# Number of columns
d = 2
# Number of qubits
qubit_num = w * d

# Create a quantum circuit
cir = Circuit("MBQC cluster state circuit")

# Apply Hadamard gate to each qubit to prepare plus state
for i in range(qubit_num):
    cir.h(i)

# Apply controlled-phase gates based on the topology of the grid
for col in range(d):
    for row in range(w):
        q = col * w + row
        # Implement controlled-phase gates between qubits in the same column
        if row < w - 1:
            cir.cz([q, q + 1])
    if col < d - 1:
        # Implement controlled-phase gates between qubits in adjacent columns
        for row in range(w):
            q = col * w + row
            cir.cz([q, q + w])

# Measure all qubits
cir.measure()
# Print the circuit
cir.print_circuit()


# Get the biadjacency matrix and the candidate matrix of the simplified graph
# of the quantum circuit through boolean matrix multiplication
b_circuit, c_circuit = cir.get_biadjacency_and_candidate_matrices()


# Define some helper matrices to construct the biadjacency matrix and the candidate matrix
def matrix_d(k) -> numpy.ndarray:
    r"""Generate the block matrix D_k to construct the biadjacency matrix.

    Args:
        k (int): index of the block matrix

    Returns:
        numpy.ndarray: the block matrix D with respect to the input index
    """
    d_k = numpy.zeros((w, w), dtype=int)
    for m in range(0, w):
        for n in range(max(m - k - 1, 0), w):
            d_k[m][n] = 1
    return d_k


def matrix_g(k) -> numpy.ndarray:
    r"""Generate the block matrix G_k to construct the candidate matrix.

    Args:
        k (int): index of the block matrix

    Returns:
        numpy.ndarray: the block matrix G with respect to the input index
    """
    g_k = numpy.zeros((w, w), dtype=int)
    for m in range(0, w):
        for n in range(m + k + 2, w):
            g_k[m][n] = 1
    return g_k


# Construct the biadjacency matrix based on theoretical analysis.
b_theory = numpy.zeros((qubit_num, qubit_num), dtype=int)
for i in range(1, d):
    e = numpy.zeros((d, d), dtype=int)
    e[i][i - 1] = 1
    b_theory += numpy.kron(e, numpy.identity(w, dtype=int))
for i in range(0, d):
    for j in range(0, d - i):
        e = numpy.zeros((d, d), dtype=int)
        e[i][i + j] = 1
        b_theory += numpy.kron(e, matrix_d(j))

# Verify if two biadjacency matrices generated by different approaches are identical
b_difference = b_circuit - b_theory
print("\nThe biadjacency matrices generated by different approaches are identical:", numpy.all(b_difference == 0))

# Construct the candidate matrix based on theoretical analysis.
c_theory = numpy.zeros((qubit_num, qubit_num), dtype=int)
for i in range(0, d):
    for j in range(0, i + 1):
        e = numpy.zeros((d, d), dtype=int)
        e[i][i - j] = 1
        c_theory += numpy.kron(e, matrix_g(j))
for i in range(0, d - 1):
    e = numpy.zeros((d, d), dtype=int)
    e[i][i + 1] = 1
    c_theory += numpy.kron(e, (numpy.ones((w, w), dtype=int) - numpy.identity(w, dtype=int)))
for i in range(0, d):
    for j in range(i + 2, d):
        e = numpy.zeros((d, d), dtype=int)
        e[i][j] = 1
        c_theory += numpy.kron(e, numpy.ones((w, w), dtype=int))

# Verify if two candidate matrices generated by different approaches are identical
c_difference = c_circuit - c_theory
print("\nThe candidate matrices generated by different approaches are identical:", numpy.all(c_difference == 0))


# Construct the matrix corresponding to the added edges in the optimal compilation
op_matrix = numpy.zeros([qubit_num, qubit_num], dtype=int)
for i in range(0, qubit_num - w - 1):
    op_matrix[i][i + w + 1] += 1

# Construct the adjacency matrix corresponding to the optimal compilation
zero_matrix = numpy.zeros([qubit_num, qubit_num], dtype=int)
adjacency_matrix = numpy.block([[zero_matrix, b_circuit], [op_matrix, zero_matrix]])

# Iteratively calculate the power of the adjacency matrix
nilpotent = reduce(numpy.matmul, [adjacency_matrix for _ in range(2 * qubit_num)])

# Check whether the adjacency matrix corresponding to the optimal compilation is nilpotent
print("\nThe adjacency matrix corresponding to the optimal compilation is nilpotent:", numpy.all(nilpotent == 0))