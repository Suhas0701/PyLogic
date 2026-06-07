from typing import TYPE_CHECKING
from .exceptions import InvalidConnectionError

if TYPE_CHECKING:
    from .pins import OutputPin, InputPin

class Wire:
    def __init__(self, source: 'OutputPin', target: 'InputPin'):
        if target.connected_wire is not None:
            raise InvalidConnectionError(f"Input pin {target.name} is already connected.")
            
        # Hardware Validation: Prevent 8-bit to 1-bit direct crashes
        if getattr(source, 'bit_width', 1) != getattr(target, 'bit_width', 1):
            raise InvalidConnectionError(f"Width mismatch: {getattr(source, 'bit_width', 1)}-bit output to {getattr(target, 'bit_width', 1)}-bit input. Use a Splitter.")

        self.source = source
        self.target = target
        self.source.connect(self)
        self.target.connected_wire = self

    def propagate(self, state: int) -> None:
        self.target.set_state(state)
        
    def disconnect(self) -> None:
        if self in self.source.connected_wires:
            self.source.connected_wires.remove(self)
        self.target.connected_wire = None
        self.target.set_state(0)