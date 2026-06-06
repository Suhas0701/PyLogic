from typing import TYPE_CHECKING
from .types import LogicState
from .exceptions import InvalidConnectionError

if TYPE_CHECKING:
    from .pins import OutputPin, InputPin

class Wire:
    def __init__(self, source: 'OutputPin', target: 'InputPin'):
        if target.connected_wire is not None:
            raise InvalidConnectionError(f"Input pin {target.name} is already connected.")
        self.source = source
        self.target = target
        self.source.connect(self)
        self.target.connected_wire = self

    def propagate(self, state: LogicState) -> None:
        self.target.set_state(state)
        
    def disconnect(self) -> None:
        if self in self.source.connected_wires:
            self.source.connected_wires.remove(self)
        self.target.connected_wire = None
        self.target.set_state(LogicState.UNDEFINED)
