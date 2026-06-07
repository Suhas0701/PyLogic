from .base import BaseComponent

class ANDGate(BaseComponent):
    def __init__(self, component_id: str, input_count: int = 2, bit_width: int = 1):
        super().__init__(component_id)
        for i in range(input_count):
            self.add_input(f"in_{i}", bit_width)
        self.add_output("out", bit_width)

    def evaluate(self) -> None:
        states = list(self.inputs.values())
        if not states: return
        result = states[0].state
        for pin in states[1:]:
            result &= pin.state
        self.outputs["out"].set_state(result)

class ORGate(BaseComponent):
    def __init__(self, component_id: str, input_count: int = 2, bit_width: int = 1):
        super().__init__(component_id)
        for i in range(input_count):
            self.add_input(f"in_{i}", bit_width)
        self.add_output("out", bit_width)

    def evaluate(self) -> None:
        states = list(self.inputs.values())
        if not states: return
        result = states[0].state
        for pin in states[1:]:
            result |= pin.state
        self.outputs["out"].set_state(result)

class NOTGate(BaseComponent):
    def __init__(self, component_id: str, bit_width: int = 1):
        super().__init__(component_id)
        self.add_input("in", bit_width)
        self.add_output("out", bit_width)

    def evaluate(self) -> None:
        in_pin = self.inputs["in"]
        result = (~in_pin.state) & in_pin.max_value
        self.outputs["out"].set_state(result)

class Splitter(BaseComponent):
    """Phase 10: Splits an N-bit bus into N 1-bit lines."""
    def __init__(self, component_id: str, bit_width: int):
        super().__init__(component_id)
        self.bit_width = bit_width
        self.add_input("in", bit_width)
        for i in range(bit_width):
            self.add_output(f"out_{i}", 1)

    def evaluate(self) -> None:
        in_val = self.inputs["in"].state
        for i in range(self.bit_width):
            bit_val = (in_val >> i) & 1
            self.outputs[f"out_{i}"].set_state(bit_val)


class Merger(BaseComponent):
    """Phase 10: Merges N 1-bit lines into an N-bit bus."""
    def __init__(self, component_id: str, bit_width: int):
        super().__init__(component_id)
        self.bit_width = bit_width
        for i in range(bit_width):
            self.add_input(f"in_{i}", 1)
        self.add_output("out", bit_width)

    def evaluate(self) -> None:
        result = 0
        for i in range(self.bit_width):
            # Read each 1-bit input and shift it into its proper position in the integer
            bit_val = self.inputs[f"in_{i}"].state
            result |= (bit_val << i)
        self.outputs["out"].set_state(result)