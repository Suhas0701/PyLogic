from enum import Enum
from typing import List, Set
from collections import deque
from ..components.base import BaseComponent
from ..exceptions import CircuitLoopError
from ..events import EventDispatcher

class SimState(Enum):
    PLAYING = 1
    PAUSED = 2

class SimulationController(EventDispatcher):
    def __init__(self):
        super().__init__()
        self.components: List[BaseComponent] = []
        self.clocks: List[BaseComponent] = []
        self._eval_queue: deque = deque()
        self._in_queue: Set[BaseComponent] = set()
        self.state = SimState.PLAYING

    def add_component(self, component: BaseComponent) -> None:
        component.bind_engine(self)
        self.components.append(component)
        if component.__class__.__name__ == "ClockGenerator":
            self.clocks.append(component)

    def queue_evaluation(self, component: BaseComponent) -> None:
        if component not in self._in_queue:
            self._eval_queue.append(component)
            self._in_queue.add(component)

    def step(self) -> bool:
        if not self._eval_queue: return False
        comp = self._eval_queue.popleft()
        self._in_queue.remove(comp)
        comp.evaluate()
        self.emit("component_evaluated", comp)
        return True

    def run_until_stable(self, max_steps: int = 1000) -> None:
        if self.state == SimState.PAUSED: return
        steps = 0
        while self._eval_queue:
            if steps > max_steps:
                self.emit("error", "Simulation halted: Infinite combinational oscillation detected.")
                self._eval_queue.clear()
                self._in_queue.clear()
                break
            self.step()
            steps += 1
        self.emit("state_stabilized")

    def tick_clocks(self) -> None:
        """Advances global timing by toggling all ClockGenerators."""
        if self.state == SimState.PAUSED: return
        for clock in self.clocks:
            clock.tick()
        self.emit("clock_tick")
        self.run_until_stable()

    def play(self) -> None:
        self.state = SimState.PLAYING
        self.run_until_stable()
        self.emit("simulation_started")

    def pause(self) -> None:
        self.state = SimState.PAUSED
        self.emit("simulation_paused")

    def detect_loops(self) -> None:
        visited, recursion_stack = set(), set()

        def dfs(comp: BaseComponent) -> None:
            if comp in recursion_stack:
                if not comp.is_sequential:
                    raise CircuitLoopError("Combinational loop detected.")
                return
            if comp in visited: return
            visited.add(comp)
            recursion_stack.add(comp)

            for out_pin in comp.outputs.values():
                for wire in out_pin.connected_wires:
                    dfs(wire.target.parent)
            recursion_stack.remove(comp)

        for comp in self.components:
            if comp not in visited: dfs(comp)
