import pytest
from app.engine.types import LogicState
from app.engine.simulation.controller import SimulationController
from app.engine.components.gates import ANDGate, NOTGate
from app.engine.components.io import ToggleSwitch
from app.engine.wire import Wire
from app.engine.debugger import EngineDebugger

def test_combinational_propagation_chain():
    engine = SimulationController()
    debugger = EngineDebugger(engine)
    
    sw1 = ToggleSwitch("sw1")
    sw2 = ToggleSwitch("sw2")
    and1 = ANDGate("and1")
    not1 = NOTGate("not1")
    
    engine.add_component(sw1)
    engine.add_component(sw2)
    engine.add_component(and1)
    engine.add_component(not1)
    
    Wire(sw1.outputs["out"], and1.inputs["in_0"])
    Wire(sw2.outputs["out"], and1.inputs["in_1"])
    Wire(and1.outputs["out"], not1.inputs["in"])
    
    # FIXED: Manually initialize states for direct backend testing
    and1.inputs["in_0"].set_state(sw1.outputs["out"].state)
    and1.inputs["in_1"].set_state(sw2.outputs["out"].state)
    not1.inputs["in"].set_state(LogicState.LOW) # AND evaluates to LOW default
    
    engine.queue_evaluation(and1)
    engine.queue_evaluation(not1)
    
    engine.run_until_stable()
    assert not1.outputs["out"].state == LogicState.HIGH
    
    # Turn both switches HIGH
    sw1._state = LogicState.HIGH
    sw2._state = LogicState.HIGH
    
    # Force propagation
    sw1.toggle()
    sw1.toggle() 
    sw2.toggle()
    sw2.toggle()
    
    engine.run_until_stable()
    
    assert and1.outputs["out"].state == LogicState.HIGH
    assert not1.outputs["out"].state == LogicState.LOW
    assert len(debugger.history) > 0
