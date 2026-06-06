import os

files = {
    "app/engine/__init__.py": "",
    "app/engine/types.py": """from enum import Enum, auto

class LogicState(Enum):
    LOW = 0
    HIGH = 1
    HIGH_Z = 2
    UNDEFINED = 3

    def __bool__(self) -> bool:
        return self == LogicState.HIGH
""",
    "app/engine/exceptions.py": """class SimulationError(Exception):
    pass

class CircuitLoopError(SimulationError):
    pass

class InvalidConnectionError(SimulationError):
    pass
""",
    "app/engine/pins.py": """from typing import TYPE_CHECKING, Optional, List
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
""",
    "app/engine/wire.py": """from typing import TYPE_CHECKING
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
""",
    "app/engine/components/__init__.py": "",
    "app/engine/components/base.py": """from abc import ABC, abstractmethod
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
""",
    "app/engine/components/gates.py": """from .base import BaseComponent
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
""",
    "app/engine/simulation/__init__.py": "",
    "app/engine/simulation/controller.py": """from typing import List, Set
from collections import deque
from ..components.base import BaseComponent
from ..exceptions import CircuitLoopError

class SimulationController:
    def __init__(self):
        self.components: List[BaseComponent] = []
        self._eval_queue: deque = deque()
        self._in_queue: Set[BaseComponent] = set()

    def add_component(self, component: BaseComponent) -> None:
        component.bind_engine(self)
        self.components.append(component)

    def queue_evaluation(self, component: BaseComponent) -> None:
        if component not in self._in_queue:
            self._eval_queue.append(component)
            self._in_queue.add(component)

    def step(self) -> bool:
        if not self._eval_queue:
            return False
        comp = self._eval_queue.popleft()
        self._in_queue.remove(comp)
        comp.evaluate()
        return True

    def run_until_stable(self, max_steps: int = 10000) -> None:
        steps = 0
        while self._eval_queue:
            if steps > max_steps:
                raise RuntimeError("Simulation exceeded max steps. Possible uncontrolled oscillation.")
            self.step()
            steps += 1

    def detect_loops(self) -> None:
        visited: Set[BaseComponent] = set()
        recursion_stack: Set[BaseComponent] = set()

        def dfs(comp: BaseComponent) -> None:
            if comp in recursion_stack:
                if not comp.is_sequential:
                    raise CircuitLoopError(f"Combinational loop detected involving {comp.id}")
                return
            if comp in visited:
                return

            visited.add(comp)
            recursion_stack.add(comp)

            for out_pin in comp.outputs.values():
                for wire in out_pin.connected_wires:
                    dfs(wire.target.parent)

            recursion_stack.remove(comp)

        for comp in self.components:
            if comp not in visited:
                dfs(comp)
""",
    "app/testing/__init__.py": "",
    "app/testing/test_engine.py": """import pytest
from app.engine.types import LogicState
from app.engine.wire import Wire
from app.engine.components.gates import ANDGate, NOTGate, ORGate
from app.engine.simulation.controller import SimulationController
from app.engine.exceptions import CircuitLoopError

def test_and_gate_truth_table():
    engine = SimulationController()
    gate = ANDGate("and1")
    engine.add_component(gate)

    gate.inputs["in_0"].state = LogicState.LOW
    gate.inputs["in_1"].state = LogicState.LOW
    gate.evaluate()
    assert gate.outputs["out"].state == LogicState.LOW

    gate.inputs["in_0"].state = LogicState.HIGH
    gate.inputs["in_1"].state = LogicState.HIGH
    gate.evaluate()
    assert gate.outputs["out"].state == LogicState.HIGH

def test_signal_propagation():
    engine = SimulationController()
    and_gate = ANDGate("and1")
    not_gate = NOTGate("not1")
    
    engine.add_component(and_gate)
    engine.add_component(not_gate)
    Wire(and_gate.outputs["out"], not_gate.inputs["in"])
    
    and_gate.inputs["in_0"].state = LogicState.HIGH
    and_gate.inputs["in_1"].state = LogicState.HIGH
    
    engine.queue_evaluation(and_gate)
    engine.run_until_stable()
    
    assert not_gate.outputs["out"].state == LogicState.LOW

def test_loop_detection():
    engine = SimulationController()
    not1 = NOTGate("not1")
    not2 = NOTGate("not2")
    
    engine.add_component(not1)
    engine.add_component(not2)
    
    Wire(not1.outputs["out"], not2.inputs["in"])
    Wire(not2.outputs["out"], not1.inputs["in"])
    
    with pytest.raises(CircuitLoopError):
        engine.detect_loops()
"""
}

for filepath, content in files.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)

print("✅ Phase 1 scaffolding complete! All files created.")