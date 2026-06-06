import pytest
from app.engine.types import LogicState
from app.engine.components.gates import ANDGate, ORGate, NOTGate

def test_and_gate_truth_table():
    gate = ANDGate("test_and")
    # 0 AND 0 = 0
    gate.inputs["in_0"].set_state(LogicState.LOW)
    gate.inputs["in_1"].set_state(LogicState.LOW)
    gate.evaluate()
    assert gate.outputs["out"].state == LogicState.LOW
    
    # 1 AND 1 = 1
    gate.inputs["in_0"].set_state(LogicState.HIGH)
    gate.inputs["in_1"].set_state(LogicState.HIGH)
    gate.evaluate()
    assert gate.outputs["out"].state == LogicState.HIGH

def test_or_gate_truth_table():
    gate = ORGate("test_or")
    # 0 OR 1 = 1
    gate.inputs["in_0"].set_state(LogicState.LOW)
    gate.inputs["in_1"].set_state(LogicState.HIGH)
    gate.evaluate()
    assert gate.outputs["out"].state == LogicState.HIGH

def test_not_gate_truth_table():
    gate = NOTGate("test_not")
    gate.inputs["in"].set_state(LogicState.HIGH)
    gate.evaluate()
    assert gate.outputs["out"].state == LogicState.LOW
    
    gate.inputs["in"].set_state(LogicState.LOW)
    gate.evaluate()
    assert gate.outputs["out"].state == LogicState.HIGH
