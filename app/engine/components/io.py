from .base import BaseComponent

class ToggleSwitch(BaseComponent):
    """Interactive input source."""
    def __init__(self, component_id: str, bit_width: int = 1):
        super().__init__(component_id, is_sequential=False)
        self.add_output("out", bit_width)
        self._state = 0
        self.outputs["out"].set_state(self._state)

    def toggle(self) -> None:
        max_val = self.outputs["out"].max_value
        self._state = max_val if self._state == 0 else 0
        self.outputs["out"].set_state(self._state)

    def evaluate(self) -> None:
        self.outputs["out"].set_state(self._state)

class LED(BaseComponent):
    """Visual output sink."""
    def __init__(self, component_id: str, bit_width: int = 1):
        super().__init__(component_id, is_sequential=False)
        self.add_input("in", bit_width)
        self.is_lit = False

    def evaluate(self) -> None:
        self.is_lit = (self.inputs["in"].state > 0)