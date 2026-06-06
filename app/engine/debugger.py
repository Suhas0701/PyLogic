from .simulation.controller import SimulationController

class EngineDebugger:
    """Hooks into the EventDispatcher to trace propagation waves."""
    def __init__(self, engine: SimulationController):
        self.engine = engine
        self.steps_taken = 0
        self.history = []
        
        self.engine.on("component_evaluated", self._on_step)
        self.engine.on("state_stabilized", self._on_stable)
        self.engine.on("error", self._on_error)

    def _on_step(self, component):
        self.steps_taken += 1
        
    def _on_stable(self):
        self.history.append(f"Stabilized in {self.steps_taken} steps.")
        self.steps_taken = 0
        
    def _on_error(self, message):
        self.history.append(f"ERROR: {message}")
        self.steps_taken = 0
        
    def print_trace(self):
        for entry in self.history:
            print(f"[DEBUGGER] {entry}")
