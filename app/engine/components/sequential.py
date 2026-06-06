from .base import BaseComponent
from ..types import LogicState

class ClockGenerator(BaseComponent):
    def __init__(self, component_id: str):
        super().__init__(component_id, is_sequential=True)
        self.add_output("clk")
        self._state = LogicState.LOW
        self.outputs["clk"].set_state(self._state)

    def tick(self) -> None:
        self._state = LogicState.HIGH if self._state == LogicState.LOW else LogicState.LOW
        self.outputs["clk"].set_state(self._state)

    def evaluate(self) -> None:
        pass # Clock dictates its own state

class SRLatch(BaseComponent):
    def __init__(self, component_id: str):
        super().__init__(component_id, is_sequential=True)
        self.add_input("S")
        self.add_input("R")
        self.add_output("Q")
        self.add_output("Q_NOT")
        self._state = LogicState.LOW
        self.outputs["Q"].set_state(self._state)
        self.outputs["Q_NOT"].set_state(LogicState.HIGH)

    def evaluate(self) -> None:
        s = self.inputs["S"].state
        r = self.inputs["R"].state
        if s == LogicState.HIGH and r == LogicState.LOW:
            self._state = LogicState.HIGH
        elif s == LogicState.LOW and r == LogicState.HIGH:
            self._state = LogicState.LOW
        elif s == LogicState.HIGH and r == LogicState.HIGH:
            self._state = LogicState.UNDEFINED # Invalid state for SR Latch
            
        self.outputs["Q"].set_state(self._state)
        self.outputs["Q_NOT"].set_state(
            LogicState.LOW if self._state == LogicState.HIGH else 
            (LogicState.HIGH if self._state == LogicState.LOW else LogicState.UNDEFINED)
        )

class DFlipFlop(BaseComponent):
    def __init__(self, component_id: str):
        super().__init__(component_id, is_sequential=True)
        self.add_input("D")
        self.add_input("CLK")
        self.add_output("Q")
        self.add_output("Q_NOT")
        self._state = LogicState.LOW
        self._last_clk = LogicState.LOW
        self.outputs["Q"].set_state(self._state)
        self.outputs["Q_NOT"].set_state(LogicState.HIGH)

    def evaluate(self) -> None:
        current_clk = self.inputs["CLK"].state
        # Rising Edge Detection
        if self._last_clk == LogicState.LOW and current_clk == LogicState.HIGH:
            d_val = self.inputs["D"].state
            if d_val in (LogicState.HIGH, LogicState.LOW):
                self._state = d_val
                self.outputs["Q"].set_state(self._state)
                self.outputs["Q_NOT"].set_state(LogicState.LOW if self._state == LogicState.HIGH else LogicState.HIGH)
        
        self._last_clk = current_clk

class TFlipFlop(BaseComponent):
    def __init__(self, component_id: str):
        super().__init__(component_id, is_sequential=True)
        self.add_input("T")
        self.add_input("CLK")
        self.add_output("Q")
        self.add_output("Q_NOT")
        self._state = LogicState.LOW
        self._last_clk = LogicState.LOW
        self.outputs["Q"].set_state(self._state)
        self.outputs["Q_NOT"].set_state(LogicState.HIGH)

    def evaluate(self) -> None:
        current_clk = self.inputs["CLK"].state
        # Rising Edge Detection
        if self._last_clk == LogicState.LOW and current_clk == LogicState.HIGH:
            t_val = self.inputs["T"].state
            if t_val == LogicState.HIGH:
                self._state = LogicState.LOW if self._state == LogicState.HIGH else LogicState.HIGH
                self.outputs["Q"].set_state(self._state)
                self.outputs["Q_NOT"].set_state(LogicState.LOW if self._state == LogicState.HIGH else LogicState.HIGH)
        
        self._last_clk = current_clk
