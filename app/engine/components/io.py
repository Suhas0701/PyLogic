from .base import BaseComponent
from ..types import LogicState

class ToggleSwitch(BaseComponent):
    """Interactive input source."""
    def __init__(self, component_id: str):
        super().__init__(component_id, is_sequential=False)
        self.add_output("out")
        self._state = LogicState.LOW
        self.outputs["out"].set_state(self._state)

    def toggle(self) -> None:
        self._state = LogicState.HIGH if self._state == LogicState.LOW else LogicState.LOW
        # Changing output state automatically propagates to wires and queues downstream components
        self.outputs["out"].set_state(self._state)

    def evaluate(self) -> None:
        self.outputs["out"].set_state(self._state)

class LED(BaseComponent):
    """Visual output sink."""
    def __init__(self, component_id: str):
        super().__init__(component_id, is_sequential=False)
        self.add_input("in")
        self.is_lit = False

    def evaluate(self) -> None:
        self.is_lit = (self.inputs["in"].state == LogicState.HIGH)
