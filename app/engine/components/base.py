from abc import ABC, abstractmethod
from typing import Dict, TYPE_CHECKING, Optional
from ..pins import InputPin, OutputPin
from ..types import LogicState

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

    def add_input(self, name: str) -> None:
        self.inputs[name] = InputPin(name, self)

    def add_output(self, name: str) -> None:
        self.outputs[name] = OutputPin(name, self)

    @abstractmethod
    def evaluate(self) -> None:
        pass

    def reset(self) -> None:
        for pin in self.inputs.values():
            pin.state = LogicState.UNDEFINED
        for pin in self.outputs.values():
            pin.set_state(LogicState.UNDEFINED)
