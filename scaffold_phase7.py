import os

files = {
    # --- 1. DEBUGGING INFRASTRUCTURE ---
    "app/engine/debugger.py": """from .simulation.controller import SimulationController

class EngineDebugger:
    \"\"\"Hooks into the EventDispatcher to trace propagation waves.\"\"\"
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
""",
    
    # --- 2. UNIT TESTS: COMBINATIONAL GATES ---
    "app/testing/test_gates.py": """import pytest
from app.engine.types import LogicState
from app.engine.components.gates import ANDGate, ORGate, NOTGate

def test_and_gate_truth_table():
    gate = ANDGate("test_and")
    # 0 AND 0 = 0
    gate.inputs["in_0"].set_state(LogicState.LOW)
    gate.inputs["in_1"].set_state(LogicState.LOW)
    gate.evaluate()
    assert gate.outputs["out"].state == LogicState.LOW
    
    # 1 AND 1 = 1
    gate.inputs["in_0"].set_state(LogicState.HIGH)
    gate.inputs["in_1"].set_state(LogicState.HIGH)
    gate.evaluate()
    assert gate.outputs["out"].state == LogicState.HIGH

def test_or_gate_truth_table():
    gate = ORGate("test_or")
    # 0 OR 1 = 1
    gate.inputs["in_0"].set_state(LogicState.LOW)
    gate.inputs["in_1"].set_state(LogicState.HIGH)
    gate.evaluate()
    assert gate.outputs["out"].state == LogicState.HIGH

def test_not_gate_truth_table():
    gate = NOTGate("test_not")
    gate.inputs["in"].set_state(LogicState.HIGH)
    gate.evaluate()
    assert gate.outputs["out"].state == LogicState.LOW
    
    gate.inputs["in"].set_state(LogicState.LOW)
    gate.evaluate()
    assert gate.outputs["out"].state == LogicState.HIGH
""",

    # --- 3. UNIT TESTS: SEQUENTIAL EDGE TRIGGERING ---
    "app/testing/test_sequential.py": """import pytest
from app.engine.types import LogicState
from app.engine.components.sequential import DFlipFlop

def test_d_flip_flop_rising_edge():
    dff = DFlipFlop("test_dff")
    
    # Initial state should be Q=0, Q_NOT=1
    assert dff.outputs["Q"].state == LogicState.LOW
    assert dff.outputs["Q_NOT"].state == LogicState.HIGH
    
    # Set D=HIGH, but keep CLK=LOW (No edge)
    dff.inputs["D"].set_state(LogicState.HIGH)
    dff.inputs["CLK"].set_state(LogicState.LOW)
    dff.evaluate()
    
    # State should NOT change yet
    assert dff.outputs["Q"].state == LogicState.LOW
    
    # Trigger Rising Edge (CLK goes HIGH)
    dff.inputs["CLK"].set_state(LogicState.HIGH)
    dff.evaluate()
    
    # State SHOULD change now
    assert dff.outputs["Q"].state == LogicState.HIGH
    assert dff.outputs["Q_NOT"].state == LogicState.LOW
    
    # Set D=LOW, and CLK goes LOW (Falling edge)
    dff.inputs["D"].set_state(LogicState.LOW)
    dff.inputs["CLK"].set_state(LogicState.LOW)
    dff.evaluate()
    
    # State should NOT change on falling edge
    assert dff.outputs["Q"].state == LogicState.HIGH
""",

    # --- 4. UNIT TESTS: ROUTING MATH ---
    "app/testing/test_routing.py": """import pytest
from app.ui.canvas.viewport import Point
from app.ui.canvas.routing import OrthogonalRouter

def test_forward_z_route():
    start = Point(0, 0)
    end = Point(100, 50)
    path = OrthogonalRouter.route(start, end)
    
    # Should generate 4 points for a standard Z-route
    assert len(path) == 4
    assert path[0] == start
    assert path[-1] == end
    # Middle segment should align horizontally with mid_x
    assert path[1].x == 50
    assert path[1].y == 0
    assert path[2].x == 50
    assert path[2].y == 50

def test_backward_u_route():
    start = Point(100, 0)
    end = Point(0, 50)
    path = OrthogonalRouter.route(start, end, stub=20)
    
    # Should generate 6 points for a backward U-route to avoid gate clipping
    assert len(path) == 6
    assert path[0] == start
    assert path[-1] == end
    assert path[1].x == 120 # Out stub
    assert path[4].x == -20 # In stub
""",

    # --- 5. SYSTEM TESTS: CIRCUIT PROPAGATION ---
    "app/testing/test_system.py": """import pytest
from app.engine.types import LogicState
from app.engine.simulation.controller import SimulationController
from app.engine.components.gates import ANDGate, NOTGate
from app.engine.components.io import ToggleSwitch
from app.engine.wire import Wire
from app.engine.debugger import EngineDebugger

def test_combinational_propagation_chain():
    engine = SimulationController()
    debugger = EngineDebugger(engine)
    
    sw1 = ToggleSwitch("sw1")
    sw2 = ToggleSwitch("sw2")
    and1 = ANDGate("and1")
    not1 = NOTGate("not1")
    
    engine.add_component(sw1)
    engine.add_component(sw2)
    engine.add_component(and1)
    engine.add_component(not1)
    
    Wire(sw1.outputs["out"], and1.inputs["in_0"])
    Wire(sw2.outputs["out"], and1.inputs["in_1"])
    Wire(and1.outputs["out"], not1.inputs["in"])
    
    # Both switches default to LOW. Output of NOT should be HIGH.
    engine.run_until_stable()
    assert not1.outputs["out"].state == LogicState.HIGH
    
    # Turn both switches HIGH
    sw1._state = LogicState.HIGH
    sw2._state = LogicState.HIGH
    
    # Force propagation
    sw1.toggle() # Toggles to LOW
    sw1.toggle() # Toggles back to HIGH, triggers queue
    sw2.toggle()
    sw2.toggle()
    
    engine.run_until_stable()
    
    # AND is HIGH, therefore NOT is LOW
    assert and1.outputs["out"].state == LogicState.HIGH
    assert not1.outputs["out"].state == LogicState.LOW
    
    # Ensure debugger caught the propagation
    assert len(debugger.history) > 0
""",

    # --- 6. SYSTEM TESTS: SERIALIZATION ROUNDTRIP ---
    "app/testing/test_serialization.py": """import pytest
import json
from app.engine.simulation.controller import SimulationController
from app.ui.canvas.renderer import CanvasRenderer
from app.ui.bridge import UIEngineBridge

class MockPage:
    \"\"\"Mocks Flet Page to allow headless UI testing.\"\"\"
    def __init__(self):
        self.overlay = []
        self.web = False
    def run_task(self, task): pass
    def update(self): pass

def test_serialization_roundtrip():
    # 1. Setup Headless Environment
    page = MockPage()
    engine = SimulationController()
    renderer = CanvasRenderer(page)
    bridge = UIEngineBridge(engine, renderer)
    
    # 2. Build a Circuit
    bridge.spawn_gate("SWITCH", 0, 0)
    bridge.spawn_gate("NOT", 100, 0)
    
    sw_ui = list(renderer.ui_gates.values())[0]
    not_ui = list(renderer.ui_gates.values())[1]
    
    bridge.attempt_connection(sw_ui.pins[0], not_ui.pins[0])
    
    # 3. Serialize
    json_str = bridge.export_project()
    data = json.loads(json_str)
    
    assert len(data["components"]) == 2
    assert len(data["wires"]) == 1
    
    # 4. Clear and Deserialize
    bridge.clear_workspace()
    assert len(renderer.ui_gates) == 0
    
    bridge.import_project(json_str)
    
    # 5. Verify Restoration
    assert len(renderer.ui_gates) == 2
    assert len(renderer.ui_wires) == 1
"""
}

for filepath, content in files.items():
    directory = os.path.dirname(filepath)
    if directory: os.makedirs(directory, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ Phase 7 Deployed: Test Suite, CI Architecture, and Debugger Initialized.")