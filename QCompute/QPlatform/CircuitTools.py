#!/usr/bin/python3
# -*- coding: utf8 -*-

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
Circuit tools
"""
from typing import List, TYPE_CHECKING, Tuple, Optional

from QCompute.QPlatform import Error, ModuleErrorCode
from QCompute.QPlatform.ProcedureParameterPool import ProcedureParameterStorage
from QCompute.QPlatform.QOperation.Barrier import BarrierOP
from QCompute.QPlatform.QOperation.CompositeGate import CompositeGateOP
from QCompute.QPlatform.QOperation.CustomizedGate import CustomizedGateOP
from QCompute.QPlatform.QOperation.FixedGate import FixedGateOP
from QCompute.QPlatform.QOperation.Measure import MeasureOP
from QCompute.QPlatform.QOperation.QProcedure import QProcedureOP
from QCompute.QPlatform.QOperation.RotationGate import RotationGateOP
from QCompute.QPlatform.Utilities import numpyMatrixToProtobufMatrix
from QCompute.QProtobuf import PBProgram, PBCircuitLine, PBFixedGate, PBRotationGate, PBCompositeGate, \
    PBMeasure

if TYPE_CHECKING:
    from QCompute.QPlatform.QEnv import QEnv
    from QCompute.QPlatform.QOperation import CircuitLine, QOperation

FileErrorCode = 5


def QEnvToProtobuf(program: PBProgram, env: 'QEnv') -> None:
    head = program.head
    head.usingQRegList[:] = sorted([qReg for qReg in env.Q.registerMap.keys()])
    head.usingCRegList[:] = sorted([cReg for cReg in env.measuredCRegSet])

    body = program.body

    for circuitLine in env.circuit:
        body.circuit.append(circuitLineToProtobuf(circuitLine))

    for name, procedure in env.procedureMap.items():
        pbProcedure = body.procedureMap[name]
        pbProcedure.parameterCount = len(procedure.Parameter.parameterMap)
        pbProcedure.usingQRegList[:] = sorted([qReg for qReg in procedure.Q.registerMap.keys()])
        for circuitLine in procedure.circuit:
            pbProcedure.circuit.append(circuitLineToProtobuf(circuitLine))


def circuitLineToProtobuf(circuitLine: 'CircuitLine') -> 'PBCircuitLine':
    pbCircuitLine = PBCircuitLine()
    if isinstance(circuitLine.data, FixedGateOP):
        pbCircuitLine.fixedGate = PBFixedGate.Value(circuitLine.data.name)
    elif isinstance(circuitLine.data, RotationGateOP):
        pbCircuitLine.rotationGate = PBRotationGate.Value(circuitLine.data.name)
        argumentIdList, argumentValueList = getRotationArgumentList(circuitLine.data)
        pbCircuitLine.argumentIdList[:] = argumentIdList
        pbCircuitLine.argumentValueList[:] = argumentValueList
    elif isinstance(circuitLine.data, CustomizedGateOP):
        pbCircuitLine.customizedGate.matrix.CopyFrom(numpyMatrixToProtobufMatrix(circuitLine.data.getMatrix()))
    elif isinstance(circuitLine.data, CompositeGateOP):
        pbCircuitLine.compositeGate = PBCompositeGate.Value(circuitLine.data.name)
        argumentIdList, argumentValueList = getRotationArgumentList(circuitLine.data)
        pbCircuitLine.argumentIdList[:] = argumentIdList
        pbCircuitLine.argumentValueList[:] = argumentValueList
    elif isinstance(circuitLine.data, QProcedureOP):
        pbCircuitLine.procedureName = circuitLine.data.name
        argumentIdList, argumentValueList = getRotationArgumentList(circuitLine.data)
        pbCircuitLine.argumentIdList[:] = argumentIdList
        pbCircuitLine.argumentValueList[:] = argumentValueList
    elif isinstance(circuitLine.data, MeasureOP):
        pbCircuitLine.measure.type = PBMeasure.Type.Value(circuitLine.data.name)
        pbCircuitLine.measure.cRegList[:] = circuitLine.cRegList
    elif isinstance(circuitLine.data, BarrierOP):
        pbCircuitLine.barrier = True

    pbCircuitLine.qRegList[:] = circuitLine.qRegList
    return pbCircuitLine


def getRotationArgumentList(data: 'QOperation') -> Tuple[List[int], List[float]]:
    if not (isinstance(data, RotationGateOP) or
            isinstance(data, CompositeGateOP) or
            isinstance(data, QProcedureOP)):
        raise Error.ArgumentError('Wrong opreation type!', ModuleErrorCode, FileErrorCode, 1)
    argumentIdList: List[int] = []
    argumentValueList: List[float] = []
    validArgumentIdList = False
    validArgumentValueList = False
    for argument in data.argumentList:
        if isinstance(argument, ProcedureParameterStorage):
            argumentIdList.append(argument.index)
            argumentValueList.append(0)
            validArgumentIdList = True
        else:
            argumentIdList.append(-1)
            argumentValueList.append(argument)
            validArgumentValueList = True
    if not validArgumentIdList:
        argumentIdList.clear()
    elif not validArgumentValueList:
        argumentValueList.clear()
    return argumentIdList, argumentValueList


def gateToProtobuf(data: 'QOperation', qRegList: List[int], cRegList: Optional[List[int]] = None) -> 'PBCircuitLine':
    ret = PBCircuitLine()
    ret.qRegList[:] = qRegList
    if data.__class__.__name__ == 'FixedGateOP':
        ret.fixedGate = PBFixedGate.Value(data.name)
    elif data.__class__.__name__ == 'RotationGateOP':
        ret.rotationGate = PBRotationGate.Value(data.name)
        argumentIdList, argumentValueList = getRotationArgumentList(data)
        ret.argumentIdList[:] = argumentIdList
        ret.argumentValueList[:] = argumentValueList
    elif data.__class__.__name__ == 'CustomizedGateOP':
        ret.customizedGate.matrix.CopyFrom(numpyMatrixToProtobufMatrix(data.getMatrix()))
    elif data.__class__.__name__ == 'CompositeGateOP':
        ret.compositeGate = PBCompositeGate.Value(data.name)
        argumentIdList, argumentValueList = getRotationArgumentList(data)
        ret.argumentIdList[:] = argumentIdList
        ret.argumentValueList[:] = argumentValueList
    elif data.__class__.__name__ == 'QProcedureOP':
        ret.procedure_name = data.name
        argumentIdList, argumentValueList = getRotationArgumentList(data)
        ret.argumentIdList[:] = argumentIdList
        ret.argumentValueList[:] = argumentValueList
    elif data.__class__.__name__ == 'MeasureOP':
        ret.measure.type = PBMeasure.Type.Value(data.name)
        ret.measure.cRegList[:] = cRegList
    elif data.__class__.__name__ == 'BarrierOP':
        ret.barrier = True
    return ret
