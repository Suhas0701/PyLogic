from abc import ABC, abstractmethod
from typing import Dict, TYPE_CHECKING, Optional
from ..pins import InputPin, OutputPin

if TYPE_CHECKING:
    from ..simulation.controller import SimulationController

class BaseComponent(ABC):
    def __init__(self, component_id: str, is_sequential: bool = False):
        self.id = component_id
        self.is_sequential = is_sequential
        self.inputs: Dict[str, InputPin] = {}
        self.outputs: Dict[str, OutputPin] = {}
        self._simulation_engine: Optional['SimulationController'] = None

    def bind_engine(self, engine: 'SimulationController') -> None:
        self._simulation_engine = engine

    def mark_dirty(self) -> None:
        if self._simulation_engine:
            self._simulation_engine.queue_evaluation(self)

    def add_input(self, name: str, bit_width: int = 1) -> None:
        self.inputs[name] = InputPin(name, self, bit_width)

    def add_output(self, name: str, bit_width: int = 1) -> None:
        self.outputs[name] = OutputPin(name, self, bit_width)

    @abstractmethod
    def evaluate(self) -> None:
        pass

    def reset(self) -> None:
        for pin in self.inputs.values():
            pin.state = 0
        for pin in self.outputs.values():
            pin.set_state(0)