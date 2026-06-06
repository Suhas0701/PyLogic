import pytest
from app.engine.types import LogicState
from app.engine.wire import Wire
from app.engine.components.gates import ANDGate, NOTGate, ORGate
from app.engine.simulation.controller import SimulationController
from app.engine.exceptions import CircuitLoopError

def test_and_gate_truth_table():
    engine = SimulationController()
    gate = ANDGate("and1")
    engine.add_component(gate)

    gate.inputs["in_0"].state = LogicState.LOW
    gate.inputs["in_1"].state = LogicState.LOW
    gate.evaluate()
    assert gate.outputs["out"].state == LogicState.LOW

    gate.inputs["in_0"].state = LogicState.HIGH
    gate.inputs["in_1"].state = LogicState.HIGH
    gate.evaluate()
    assert gate.outputs["out"].state == LogicState.HIGH

def test_signal_propagation():
    engine = SimulationController()
    and_gate = ANDGate("and1")
    not_gate = NOTGate("not1")
    
    engine.add_component(and_gate)
    engine.add_component(not_gate)
    Wire(and_gate.outputs["out"], not_gate.inputs["in"])
    
    and_gate.inputs["in_0"].state = LogicState.HIGH
    and_gate.inputs["in_1"].state = LogicState.HIGH
    
    engine.queue_evaluation(and_gate)
    engine.run_until_stable()
    
    assert not_gate.outputs["out"].state == LogicState.LOW

def test_loop_detection():
    engine = SimulationController()
    not1 = NOTGate("not1")
    not2 = NOTGate("not2")
    
    engine.add_component(not1)
    engine.add_component(not2)
    
    Wire(not1.outputs["out"], not2.inputs["in"])
    Wire(not2.outputs["out"], not1.inputs["in"])
    
    with pytest.raises(CircuitLoopError):
        engine.detect_loops()
