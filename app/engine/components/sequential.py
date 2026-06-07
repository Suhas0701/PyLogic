from .base import BaseComponent

class ClockGenerator(BaseComponent):
    def __init__(self, component_id: str):
        super().__init__(component_id, is_sequential=True)
        self.add_output("clk", 1)
        self._state = 0
        self.outputs["clk"].set_state(self._state)

    def tick(self) -> None:
        self._state = 1 if self._state == 0 else 0
        self.outputs["clk"].set_state(self._state)

    def evaluate(self) -> None:
        pass 

class SRLatch(BaseComponent):
    def __init__(self, component_id: str):
        super().__init__(component_id, is_sequential=True)
        self.add_input("S", 1)
        self.add_input("R", 1)
        self.add_output("Q", 1)
        self.add_output("Q_NOT", 1)
        self._state = 0
        self.outputs["Q"].set_state(self._state)
        self.outputs["Q_NOT"].set_state(1)

    def evaluate(self) -> None:
        s = self.inputs["S"].state
        r = self.inputs["R"].state
        
        if s == 1 and r == 0:
            self._state = 1
        elif s == 0 and r == 1:
            self._state = 0
        elif s == 1 and r == 1:
            self._state = 0 
            
        self.outputs["Q"].set_state(self._state)
        self.outputs["Q_NOT"].set_state(1 if self._state == 0 else 0)

class DFlipFlop(BaseComponent):
    def __init__(self, component_id: str):
        super().__init__(component_id, is_sequential=True)
        self.add_input("D", 1)
        self.add_input("CLK", 1)
        self.add_output("Q", 1)
        self.add_output("Q_NOT", 1)
        self._state = 0
        self._last_clk = 0
        self.outputs["Q"].set_state(self._state)
        self.outputs["Q_NOT"].set_state(1)

    def evaluate(self) -> None:
        current_clk = self.inputs["CLK"].state
        if self._last_clk == 0 and current_clk == 1:
            self._state = self.inputs["D"].state
            self.outputs["Q"].set_state(self._state)
            self.outputs["Q_NOT"].set_state(1 if self._state == 0 else 0)
        self._last_clk = current_clk

class TFlipFlop(BaseComponent):
    def __init__(self, component_id: str):
        super().__init__(component_id, is_sequential=True)
        self.add_input("T", 1)
        self.add_input("CLK", 1)
        self.add_output("Q", 1)
        self.add_output("Q_NOT", 1)
        self._state = 0
        self._last_clk = 0
        self.outputs["Q"].set_state(self._state)
        self.outputs["Q_NOT"].set_state(1)

    def evaluate(self) -> None:
        current_clk = self.inputs["CLK"].state
        if self._last_clk == 0 and current_clk == 1:
            if self.inputs["T"].state == 1:
                self._state = 0 if self._state == 1 else 1
                self.outputs["Q"].set_state(self._state)
                self.outputs["Q_NOT"].set_state(1 if self._state == 0 else 0)
        self._last_clk = current_clk