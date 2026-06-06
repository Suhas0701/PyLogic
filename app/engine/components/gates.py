from .base import BaseComponent
from ..types import LogicState

class ANDGate(BaseComponent):
    def __init__(self, component_id: str, input_count: int = 2):
        super().__init__(component_id)
        for i in range(input_count):
            self.add_input(f"in_{i}")
        self.add_output("out")

    def evaluate(self) -> None:
        states = [pin.state for pin in self.inputs.values()]
        if any(s in (LogicState.UNDEFINED, LogicState.HIGH_Z) for s in states):
            self.outputs["out"].set_state(LogicState.UNDEFINED)
            return
        is_high = all(s == LogicState.HIGH for s in states)
        self.outputs["out"].set_state(LogicState.HIGH if is_high else LogicState.LOW)

class ORGate(BaseComponent):
    def __init__(self, component_id: str, input_count: int = 2):
        super().__init__(component_id)
        for i in range(input_count):
            self.add_input(f"in_{i}")
        self.add_output("out")

    def evaluate(self) -> None:
        states = [pin.state for pin in self.inputs.values()]
        if any(s == LogicState.HIGH for s in states):
            self.outputs["out"].set_state(LogicState.HIGH)
        elif any(s in (LogicState.UNDEFINED, LogicState.HIGH_Z) for s in states):
            self.outputs["out"].set_state(LogicState.UNDEFINED)
        else:
            self.outputs["out"].set_state(LogicState.LOW)

class NOTGate(BaseComponent):
    def __init__(self, component_id: str):
        super().__init__(component_id)
        self.add_input("in")
        self.add_output("out")

    def evaluate(self) -> None:
        state = self.inputs["in"].state
        if state == LogicState.HIGH:
            self.outputs["out"].set_state(LogicState.LOW)
        elif state == LogicState.LOW:
            self.outputs["out"].set_state(LogicState.HIGH)
        else:
            self.outputs["out"].set_state(LogicState.UNDEFINED)
