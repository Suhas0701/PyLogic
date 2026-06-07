from typing import TYPE_CHECKING, Optional, List
from .exceptions import InvalidConnectionError

if TYPE_CHECKING:
    from .components.base import BaseComponent
    from .wire import Wire

class Pin:
    def __init__(self, name: str, parent: 'BaseComponent', bit_width: int = 1):
        self.name = name
        self.parent = parent
        self.bit_width = bit_width
        self.state: int = 0 

    @property
    def max_value(self) -> int:
        return (1 << self.bit_width) - 1

class InputPin(Pin):
    def __init__(self, name: str, parent: 'BaseComponent', bit_width: int = 1):
        super().__init__(name, parent, bit_width)
        self.connected_wire: Optional['Wire'] = None

    def set_state(self, state: int) -> None:
        masked_state = state & self.max_value
        if self.state != masked_state:
            self.state = masked_state
            self.parent.mark_dirty()

class OutputPin(Pin):
    def __init__(self, name: str, parent: 'BaseComponent', bit_width: int = 1):
        super().__init__(name, parent, bit_width)
        self.connected_wires: List['Wire'] = []

    def set_state(self, state: int) -> None:
        masked_state = state & self.max_value
        if self.state != masked_state:
            self.state = masked_state
            for wire in self.connected_wires:
                wire.propagate(self.state)

    def connect(self, wire: 'Wire') -> None:
        if wire not in self.connected_wires:
            self.connected_wires.append(wire)