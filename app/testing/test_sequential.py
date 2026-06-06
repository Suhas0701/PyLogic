import pytest
from app.engine.types import LogicState
from app.engine.components.sequential import DFlipFlop

def test_d_flip_flop_rising_edge():
    dff = DFlipFlop("test_dff")
    
    # Initial state should be Q=0, Q_NOT=1
    assert dff.outputs["Q"].state == LogicState.LOW
    assert dff.outputs["Q_NOT"].state == LogicState.HIGH
    
    # Set D=HIGH, but keep CLK=LOW (No edge)
    dff.inputs["D"].set_state(LogicState.HIGH)
    dff.inputs["CLK"].set_state(LogicState.LOW)
    dff.evaluate()
    
    # State should NOT change yet
    assert dff.outputs["Q"].state == LogicState.LOW
    
    # Trigger Rising Edge (CLK goes HIGH)
    dff.inputs["CLK"].set_state(LogicState.HIGH)
    dff.evaluate()
    
    # State SHOULD change now
    assert dff.outputs["Q"].state == LogicState.HIGH
    assert dff.outputs["Q_NOT"].state == LogicState.LOW
    
    # Set D=LOW, and CLK goes LOW (Falling edge)
    dff.inputs["D"].set_state(LogicState.LOW)
    dff.inputs["CLK"].set_state(LogicState.LOW)
    dff.evaluate()
    
    # State should NOT change on falling edge
    assert dff.outputs["Q"].state == LogicState.HIGH
