from typing import TYPE_CHECKING, Optional, List
from .types import LogicState
from .exceptions import InvalidConnectionError

if TYPE_CHECKING:
    from .components.base import BaseComponent
    from .wire import Wire

class Pin:
    def __init__(self, name: str, parent: 'BaseComponent'):
        self.name = name
        self.parent = parent
        self.state: LogicState = LogicState.UNDEFINED

class InputPin(Pin):
    def __init__(self, name: str, parent: 'BaseComponent'):
        super().__init__(name, parent)
        self.connected_wire: Optional['Wire'] = None

    def set_state(self, state: LogicState) -> None:
        if self.state != state:
            self.state = state
            self.parent.mark_dirty()

class OutputPin(Pin):
    def __init__(self, name: str, parent: 'BaseComponent'):
        super().__init__(name, parent)
        self.connected_wires: List['Wire'] = []

    def set_state(self, state: LogicState) -> None:
        if self.state != state:
            self.state = state
            for wire in self.connected_wires:
                wire.propagate(self.state)

    def connect(self, wire: 'Wire') -> None:
        if wire not in self.connected_wires:
            self.connected_wires.append(wire)
