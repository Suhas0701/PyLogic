import os

files = {
    "app/engine/events.py": """from typing import Callable, Dict, List

class EventDispatcher:
    \"\"\"Decoupled publisher/subscriber for Engine-to-UI communication.\"\"\"
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def on(self, event_name: str, callback: Callable) -> None:
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(callback)

    def emit(self, event_name: str, *args, **kwargs) -> None:
        for listener in self._listeners.get(event_name, []):
            listener(*args, **kwargs)
""",
    "app/engine/components/io.py": """from .base import BaseComponent
from ..types import LogicState

class ToggleSwitch(BaseComponent):
    \"\"\"Interactive input source.\"\"\"
    def __init__(self, component_id: str):
        super().__init__(component_id, is_sequential=False)
        self.add_output("out")
        self._state = LogicState.LOW
        self.outputs["out"].set_state(self._state)

    def toggle(self) -> None:
        self._state = LogicState.HIGH if self._state == LogicState.LOW else LogicState.LOW
        # Changing output state automatically propagates to wires and queues downstream components
        self.outputs["out"].set_state(self._state)

    def evaluate(self) -> None:
        self.outputs["out"].set_state(self._state)

class LED(BaseComponent):
    \"\"\"Visual output sink.\"\"\"
    def __init__(self, component_id: str):
        super().__init__(component_id, is_sequential=False)
        self.add_input("in")
        self.is_lit = False

    def evaluate(self) -> None:
        self.is_lit = (self.inputs["in"].state == LogicState.HIGH)
""",
    "app/engine/simulation/controller.py": """from enum import Enum
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
        self._eval_queue: deque = deque()
        self._in_queue: Set[BaseComponent] = set()
        self.state = SimState.PLAYING

    def add_component(self, component: BaseComponent) -> None:
        component.bind_engine(self)
        self.components.append(component)

    def queue_evaluation(self, component: BaseComponent) -> None:
        if component not in self._in_queue:
            self._eval_queue.append(component)
            self._in_queue.add(component)

    def step(self) -> bool:
        \"\"\"Executes exactly one component evaluation for fine-grained debugging.\"\"\"
        if not self._eval_queue:
            return False
        comp = self._eval_queue.popleft()
        self._in_queue.remove(comp)
        comp.evaluate()
        self.emit("component_evaluated", comp)
        return True

    def run_until_stable(self, max_steps: int = 1000) -> None:
        \"\"\"Flushes the queue synchronously. Safe because of loop detection.\"\"\"
        if self.state == SimState.PAUSED:
            return
            
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

    def play(self) -> None:
        self.state = SimState.PLAYING
        self.run_until_stable()
        self.emit("simulation_started")

    def pause(self) -> None:
        self.state = SimState.PAUSED
        self.emit("simulation_paused")

    def detect_loops(self) -> None:
        visited: Set[BaseComponent] = set()
        recursion_stack: Set[BaseComponent] = set()

        def dfs(comp: BaseComponent) -> None:
            if comp in recursion_stack:
                if not comp.is_sequential:
                    raise CircuitLoopError(f"Combinational loop detected.")
                return
            if comp in visited: return
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
    "app/ui/components/gate_ui.py": """import flet as ft
from ..canvas.viewport import Viewport, Point
from .pin_ui import UIPin
from typing import List

class UIGate:
    def __init__(self, gate_id: str, world_x: float, world_y: float, label: str, backend_comp):
        self.gate_id = gate_id
        self.backend_comp = backend_comp
        self.world_pos = Point(world_x, world_y)
        self._raw_world_x = world_x
        self._raw_world_y = world_y
        self.label = label
        self.width = 80
        self.height = 40
        self.is_selected = False
        
        self.pins: List[UIPin] = []
        
        in_count = len(backend_comp.inputs)
        for i, pin_id in enumerate(backend_comp.inputs.keys()):
            y_offset = (self.height / (in_count + 1)) * (i + 1)
            self.pins.append(UIPin(self, pin_id, True, 0, y_offset))
            
        out_count = len(backend_comp.outputs)
        for i, pin_id in enumerate(backend_comp.outputs.keys()):
            y_offset = (self.height / (out_count + 1)) * (i + 1)
            self.pins.append(UIPin(self, pin_id, False, self.width, y_offset))

        self.control = ft.Container(
            width=self.width, height=self.height,
            border_radius=5,
            border=ft.border.all(2, ft.Colors.TRANSPARENT),
            alignment=ft.Alignment(0, 0),
            content=ft.Text(self.label, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            left=0, top=0
        )
        self.viewport: 'Viewport' = None

    def bind(self, viewport: Viewport) -> None:
        self.viewport = viewport
        self.update_render_position()

    def contains(self, wx: float, wy: float) -> bool:
        return (self.world_pos.x <= wx <= self.world_pos.x + self.width and 
                self.world_pos.y <= wy <= self.world_pos.y + self.height)

    def _update_visual_state(self):
        \"\"\"Differentiates switches, LEDs, and logic gates dynamically.\"\"\"
        if self.label == "SWITCH":
            is_on = getattr(self.backend_comp, "_state", False)
            self.control.bgcolor = ft.Colors.GREEN_600 if is_on else ft.Colors.RED_900
        elif self.label == "LED":
            is_lit = getattr(self.backend_comp, "is_lit", False)
            self.control.bgcolor = ft.Colors.RED_400 if is_lit else ft.Colors.BLUE_GREY_900
            self.control.shadow = ft.BoxShadow(spread_radius=10, blur_radius=20, color=ft.Colors.RED_ACCENT_400) if is_lit else None
        else:
            self.control.bgcolor = ft.Colors.BLUE_GREY_800

    def update_render_position(self) -> None:
        if not self.viewport: return
        self._update_visual_state()
        
        sp = self.viewport.world_to_screen(self.world_pos)
        self.control.left = sp.x
        self.control.top = sp.y
        self.control.width = self.width * self.viewport.zoom
        self.control.height = self.height * self.viewport.zoom
        
        border_color = ft.Colors.AMBER_400 if self.is_selected else ft.Colors.TRANSPARENT
        self.control.border = ft.border.all(2 * self.viewport.zoom, border_color)
""",
    "app/ui/canvas/renderer.py": """import flet as ft
import flet.canvas as cv
from typing import Dict, List, Optional
from .viewport import Viewport, Point
from .routing import OrthogonalRouter
from ..components.gate_ui import UIGate
from ..components.pin_ui import UIPin
from ..components.wire_ui import UIWire

class CanvasRenderer:
    def __init__(self, page: ft.Page):
        self.page = page
        try:
            vw, vh = page.window.width, page.window.height
        except AttributeError:
            vw, vh = getattr(page, "width", 800), getattr(page, "height", 600)
            
        self.viewport = Viewport(width=vw or 800, height=vh or 600)
        self.ui_gates: Dict[str, UIGate] = {}
        self.ui_wires: List[UIWire] = []
        
        self.dragging_gate: Optional[UIGate] = None
        self.wiring_start_pin: Optional[UIPin] = None
        self.wiring_curr_wp: Optional[Point] = None
        
        self.bridge = None
        self._last_pan_x, self._last_pan_y = 0.0, 0.0
        
        self.root_stack = ft.Stack(expand=True)
        self.root_stack.controls.append(ft.Container(bgcolor=ft.Colors.GREY_900, expand=True))
        
        self.grid_canvas = cv.Canvas(expand=True)
        self.root_stack.controls.append(self.grid_canvas)
        self.wire_canvas = cv.Canvas(expand=True)
        self.root_stack.controls.append(self.wire_canvas)
        self.gates_layer = ft.Stack(expand=True)
        self.root_stack.controls.append(self.gates_layer)
        
        self.glass_pane = ft.GestureDetector(
            on_pan_start=self._on_pan_start,
            on_pan_update=self._on_pan,
            on_pan_end=self._on_pan_end,
            on_scroll=self._on_scroll,
            on_tap=self._on_tap,
            drag_interval=5,
            content=ft.Container(bgcolor="#01000000", expand=True)
        )
        self.root_stack.controls.append(self.glass_pane)
        
        # UI Toolbar for Simulation Controls
        self.toolbar = ft.Container(
            content=ft.Row([
                ft.IconButton(icon=ft.Icons.PLAY_ARROW, on_click=self._on_play, icon_color=ft.Colors.GREEN),
                ft.IconButton(icon=ft.Icons.PAUSE, on_click=self._on_pause, icon_color=ft.Colors.AMBER),
                ft.IconButton(icon=ft.Icons.SKIP_NEXT, on_click=self._on_step, icon_color=ft.Colors.BLUE),
            ]),
            top=15, left=15,
            bgcolor=ft.Colors.BLUE_GREY_900,
            border_radius=8,
            padding=5,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK54)
        )
        self.root_stack.controls.append(self.toolbar)
        
        self.view = ft.Container(content=self.root_stack, expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE)

    def bind_bridge(self, bridge):
        self.bridge = bridge

    def show_error(self, message: str):
        try:
            sb = ft.SnackBar(content=ft.Text(message, color=ft.Colors.WHITE), bgcolor=ft.Colors.RED_800)
            self.page.open(sb)
        except:
            print(f"SIMULATION ERROR: {message}")

    # --- Toolbar Actions ---
    def _on_play(self, e):
        if self.bridge: self.bridge.engine.play()
    def _on_pause(self, e):
        if self.bridge: self.bridge.engine.pause()
    def _on_step(self, e):
        if self.bridge:
            self.bridge.engine.step()
            self.update_all_components()

    def _extract_coords(self, e, is_delta=False):
        if is_delta:
            obj = getattr(e, "local_delta", getattr(e, "global_delta", None))
            if obj: return float(getattr(obj, "x", 0)), float(getattr(obj, "y", 0))
        else:
            obj = getattr(e, "local_position", getattr(e, "global_position", None))
            if obj: return float(getattr(obj, "x", 0)), float(getattr(obj, "y", 0))
            if hasattr(e, "local_x"): return float(getattr(e, "local_x", 0)), float(getattr(e, "local_y", 0))
        return 0.0, 0.0

    def add_gate(self, ui_gate: UIGate) -> None:
        self.ui_gates[ui_gate.gate_id] = ui_gate
        ui_gate.bind(self.viewport)
        self.gates_layer.controls.append(ui_gate.control)
        self.update_all_components()

    def _hit_test_pins(self, wp: Point) -> Optional[UIPin]:
        hit_radius = 20.0 / self.viewport.zoom
        closest_pin = None
        min_dist_sq = hit_radius**2
        
        for gate in self.ui_gates.values():
            for pin in gate.pins:
                pp = pin.global_pos
                dist_sq = (wp.x - pp.x)**2 + (wp.y - pp.y)**2
                if dist_sq <= min_dist_sq:
                    min_dist_sq = dist_sq
                    closest_pin = pin
        return closest_pin

    def _on_pan_start(self, e):
        x, y = self._extract_coords(e, is_delta=False)
        self._last_pan_x, self._last_pan_y = x, y
        wp = self.viewport.screen_to_world(Point(x, y))
        
        hit_pin = self._hit_test_pins(wp)
        if hit_pin:
            self.wiring_start_pin = hit_pin
            self.wiring_curr_wp = wp
            return
            
        self.dragging_gate = None
        for gate in reversed(list(self.ui_gates.values())):
            if gate.contains(wp.x, wp.y):
                self.dragging_gate = gate
                break

    def _on_pan(self, e):
        dx, dy = self._extract_coords(e, is_delta=True)
        
        if self.wiring_start_pin:
            x, y = self._extract_coords(e, is_delta=False)
            self.wiring_curr_wp = self.viewport.screen_to_world(Point(x, y))
            self.update_all_components()
            return

        if self.dragging_gate:
            g = self.dragging_gate
            g._raw_world_x += dx / self.viewport.zoom
            g._raw_world_y += dy / self.viewport.zoom
            g.world_pos = self.viewport.snap_to_grid(Point(g._raw_world_x, g._raw_world_y))
        else:
            self.viewport.pan(dx, dy)
            
        self.update_all_components()

    def _on_pan_end(self, e):
        if self.wiring_start_pin and self.wiring_curr_wp:
            target_pin = self._hit_test_pins(self.wiring_curr_wp)
            if target_pin and target_pin.gate != self.wiring_start_pin.gate:
                if target_pin.is_input != self.wiring_start_pin.is_input:
                    out_pin = self.wiring_start_pin if not self.wiring_start_pin.is_input else target_pin
                    in_pin = target_pin if target_pin.is_input else self.wiring_start_pin
                    if self.bridge:
                        self.bridge.attempt_connection(out_pin, in_pin)

        self.wiring_start_pin = None
        self.wiring_curr_wp = None
        self.dragging_gate = None
        self.update_all_components()

    def _on_scroll(self, e):
        sdy = 0.0
        if hasattr(e, "scroll_delta") and e.scroll_delta is not None: sdy = float(getattr(e.scroll_delta, "y", 0))
        elif hasattr(e, "scroll_delta_y"): sdy = float(getattr(e, "scroll_delta_y", 0))
        if sdy == 0: return
        
        factor = 1.1 if sdy < 0 else 0.9
        x, y = self._extract_coords(e, is_delta=False)
        self.viewport.apply_zoom(factor, x, y)
        self.update_all_components()

    def _on_tap(self, e):
        x, y = self._extract_coords(e, is_delta=False)
        wp = self.viewport.screen_to_world(Point(x, y))
        clicked_gate = None
        
        for gate in reversed(list(self.ui_gates.values())):
            if gate.contains(wp.x, wp.y):
                clicked_gate = gate
                break
                
        # Send interactive clicks to the Bridge (e.g., Toggle Switch)
        if clicked_gate and self.bridge:
            self.bridge.handle_interaction(clicked_gate)
            
        for g in self.ui_gates.values():
            g.is_selected = (g == clicked_gate)
        self.update_all_components()

    def _draw_grid(self):
        self.grid_canvas.shapes.clear()
        origin = self.viewport.world_to_screen(Point(0, 0))
        cross = ft.Paint(color=ft.Colors.GREEN_700, stroke_width=2)
        self.grid_canvas.shapes.append(cv.Line(origin.x-20, origin.y, origin.x+20, origin.y, cross))
        self.grid_canvas.shapes.append(cv.Line(origin.x, origin.y-20, origin.x, origin.y+20, cross))
        
        dot = ft.Paint(color=ft.Colors.WHITE24, style=ft.PaintingStyle.FILL)
        for x in range(-2000, 2001, 100):
            for y in range(-2000, 2001, 100):
                if x == 0 and y == 0: continue
                sp = self.viewport.world_to_screen(Point(x, y))
                if -50 < sp.x < self.viewport.width + 50 and -50 < sp.y < self.viewport.height + 50:
                    self.grid_canvas.shapes.append(cv.Circle(sp.x, sp.y, max(1, 1.5 * self.viewport.zoom), dot))
        self.grid_canvas.update()

    def _draw_wires_and_pins(self):
        self.wire_canvas.shapes.clear()
        z = self.viewport.zoom
        
        for uw in self.ui_wires:
            color = uw.get_color()
            paint = ft.Paint(color=color, stroke_width=max(2, 3*z), stroke_cap=ft.StrokeCap.ROUND)
            path = OrthogonalRouter.route(uw.source_pin.global_pos, uw.target_pin.global_pos)
            for i in range(len(path) - 1):
                p1 = self.viewport.world_to_screen(path[i])
                p2 = self.viewport.world_to_screen(path[i+1])
                self.wire_canvas.shapes.append(cv.Line(p1.x, p1.y, p2.x, p2.y, paint))

        if self.wiring_start_pin and self.wiring_curr_wp:
            temp_paint = ft.Paint(color=ft.Colors.GREY_500, stroke_width=2*z)
            path = OrthogonalRouter.route(self.wiring_start_pin.global_pos, self.wiring_curr_wp)
            for i in range(len(path) - 1):
                p1 = self.viewport.world_to_screen(path[i])
                p2 = self.viewport.world_to_screen(path[i+1])
                self.wire_canvas.shapes.append(cv.Line(p1.x, p1.y, p2.x, p2.y, temp_paint))

        pin_paint_in = ft.Paint(color=ft.Colors.BLUE_200, style=ft.PaintingStyle.FILL)
        pin_paint_out = ft.Paint(color=ft.Colors.GREEN_200, style=ft.PaintingStyle.FILL)
        
        for gate in self.ui_gates.values():
            for pin in gate.pins:
                sp = self.viewport.world_to_screen(pin.global_pos)
                paint = pin_paint_in if pin.is_input else pin_paint_out
                self.wire_canvas.shapes.append(cv.Circle(sp.x, sp.y, pin.radius * z, paint))
                
        self.wire_canvas.update()

    def update_all_components(self) -> None:
        try:
            self.viewport.width = self.page.window.width
            self.viewport.height = self.page.window.height
        except: pass
        
        self._draw_grid() 
        self._draw_wires_and_pins()
        for gate in self.ui_gates.values():
            gate.update_render_position()
        self.view.update()
""",
    "app/ui/bridge.py": """from typing import Dict
from app.engine.simulation.controller import SimulationController
from app.engine.components.gates import ANDGate, ORGate, NOTGate
from app.engine.components.io import ToggleSwitch, LED
from app.engine.wire import Wire
from app.engine.exceptions import InvalidConnectionError, CircuitLoopError
from app.ui.canvas.renderer import CanvasRenderer
from app.ui.components.gate_ui import UIGate
from app.ui.components.pin_ui import UIPin
from app.ui.components.wire_ui import UIWire
import uuid

class UIEngineBridge:
    def __init__(self, engine: SimulationController, renderer: CanvasRenderer):
        self.engine = engine
        self.renderer = renderer
        self.renderer.bind_bridge(self)
        
        # Subscribe UI to Engine events
        self.engine.on("state_stabilized", self._on_engine_stabilized)
        self.engine.on("error", self._on_engine_error)
        
        self.gate_types = {
            "AND": ANDGate,
            "OR": ORGate,
            "NOT": NOTGate,
            "SWITCH": ToggleSwitch,
            "LED": LED
        }

    def _on_engine_stabilized(self):
        self.renderer.update_all_components()

    def _on_engine_error(self, message: str):
        self.renderer.show_error(message)

    def spawn_gate(self, gate_type: str, world_x: float, world_y: float) -> None:
        gate_id = str(uuid.uuid4())
        backend_gate = self.gate_types[gate_type.upper()](gate_id)
        self.engine.add_component(backend_gate)
        ui_gate = UIGate(gate_id, world_x, world_y, label=gate_type.upper(), backend_comp=backend_gate)
        self.renderer.add_gate(ui_gate)

    def attempt_connection(self, out_uipin: UIPin, in_uipin: UIPin) -> None:
        try:
            backend_source = out_uipin.gate.backend_comp.outputs[out_uipin.pin_id]
            backend_target = in_uipin.gate.backend_comp.inputs[in_uipin.pin_id]
            
            Wire(backend_source, backend_target)
            self.engine.detect_loops()
            
            ui_wire = UIWire(out_uipin, in_uipin, backend_source)
            self.renderer.ui_wires.append(ui_wire)
            
            # Flush queue to propagate the new connection
            self.engine.run_until_stable()
            
        except InvalidConnectionError as e:
            self.renderer.show_error(str(e))
        except CircuitLoopError as e:
            self.renderer.show_error(str(e))
            backend_target.connected_wire.disconnect()
            
        self.renderer.update_all_components()

    def handle_interaction(self, ui_gate: UIGate) -> None:
        \"\"\"Routes UI clicks to interactive backend components.\"\"\"
        if isinstance(ui_gate.backend_comp, ToggleSwitch):
            ui_gate.backend_comp.toggle()
            # Orchestrator decides if this propagates instantly (PLAY) or waits (PAUSE)
            self.engine.run_until_stable()
            self.renderer.update_all_components()
""",
    "main.py": """import flet as ft
from app.engine.simulation.controller import SimulationController
from app.ui.canvas.renderer import CanvasRenderer
from app.ui.bridge import UIEngineBridge

def main(page: ft.Page):
    page.title = "PyLogic Simulator"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK

    engine = SimulationController()
    renderer = CanvasRenderer(page)
    bridge = UIEngineBridge(engine, renderer)

    page.add(renderer.view)

    # Spawn interactive test bench
    bridge.spawn_gate("SWITCH", 100, 100)
    bridge.spawn_gate("SWITCH", 100, 200)
    bridge.spawn_gate("AND", 300, 150)
    bridge.spawn_gate("LED", 500, 150)

if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    else:
        ft.app(main)
"""
}

for filepath, content in files.items():
    directory = os.path.dirname(filepath)
    if directory: os.makedirs(directory, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ Phase 4 Scaffolding Complete! Engine events, Controls, and I/O integrated.")