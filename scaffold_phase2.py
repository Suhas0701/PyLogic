import os

files = {
    "app/ui/__init__.py": "",
    "app/ui/canvas/__init__.py": "",
    "app/ui/components/__init__.py": "",
    "app/ui/canvas/viewport.py": """from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

class Viewport:
    def __init__(self, width: float = 800, height: float = 600):
        self.camera = Point(0, 0)
        self.zoom: float = 1.0
        self.grid_size: int = 20
        self.width = width
        self.height = height

    def world_to_screen(self, world_pos: Point) -> Point:
        sx = (world_pos.x - self.camera.x) * self.zoom
        sy = (world_pos.y - self.camera.y) * self.zoom
        return Point(sx, sy)

    def screen_to_world(self, screen_pos: Point) -> Point:
        wx = (screen_pos.x / self.zoom) + self.camera.x
        wy = (screen_pos.y / self.zoom) + self.camera.y
        return Point(wx, wy)

    def pan(self, dx_screen: float, dy_screen: float) -> None:
        self.camera.x -= dx_screen / self.zoom
        self.camera.y -= dy_screen / self.zoom

    def apply_zoom(self, factor: float, focal_screen_x: float, focal_screen_y: float) -> None:
        new_zoom = max(0.2, min(3.0, self.zoom * factor))
        if new_zoom == self.zoom: return
        world_focal = self.screen_to_world(Point(focal_screen_x, focal_screen_y))
        self.zoom = new_zoom
        self.camera.x = world_focal.x - (focal_screen_x / self.zoom)
        self.camera.y = world_focal.y - (focal_screen_y / self.zoom)

    def snap_to_grid(self, world_pos: Point) -> Point:
        snapped_x = round(world_pos.x / self.grid_size) * self.grid_size
        snapped_y = round(world_pos.y / self.grid_size) * self.grid_size
        return Point(snapped_x, snapped_y)
""",
    "app/ui/components/gate_ui.py": """import flet as ft
from ..canvas.viewport import Viewport, Point

class UIGate:
    def __init__(self, gate_id: str, world_x: float, world_y: float, label: str):
        self.gate_id = gate_id
        self.world_pos = Point(world_x, world_y)
        self._raw_world_x = world_x
        self._raw_world_y = world_y
        self.label = label
        self.width = 80
        self.height = 40
        self.is_selected = False
        
        self.control = ft.Container(
            width=self.width,
            height=self.height,
            bgcolor=ft.Colors.BLUE_GREY_800,
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

    def update_render_position(self) -> None:
        if not self.viewport: return
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
from typing import Dict
from .viewport import Viewport, Point
from ..components.gate_ui import UIGate

class CanvasRenderer:
    def __init__(self, page: ft.Page):
        self.page = page
        try:
            vw, vh = page.window.width, page.window.height
        except AttributeError:
            vw, vh = getattr(page, "width", 800), getattr(page, "height", 600)
            
        self.viewport = Viewport(width=vw or 800, height=vh or 600)
        self.ui_gates: Dict[str, UIGate] = {}
        self.dragging_gate: UIGate = None
        
        self.root_stack = ft.Stack(expand=True)
        self.root_stack.controls.append(ft.Container(bgcolor=ft.Colors.GREY_900, expand=True))
        
        self.grid_canvas = cv.Canvas(expand=True)
        self.root_stack.controls.append(self.grid_canvas)
        
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
        self.view = ft.Container(content=self.root_stack, expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE)

    def add_gate(self, ui_gate: UIGate) -> None:
        self.ui_gates[ui_gate.gate_id] = ui_gate
        ui_gate.bind(self.viewport)
        self.gates_layer.controls.append(ui_gate.control)
        self.update_all_components()

    def _extract_coords(self, e, is_delta=False):
        \"\"\"Extracts coordinates from the new nested Flet 0.23+ API.\"\"\"
        if is_delta:
            # Check for the new local_delta object
            obj = getattr(e, "local_delta", getattr(e, "global_delta", None))
            if obj: return float(getattr(obj, "x", 0)), float(getattr(obj, "y", 0))
        else:
            # Check for the new local_position object
            obj = getattr(e, "local_position", getattr(e, "global_position", None))
            if obj: return float(getattr(obj, "x", 0)), float(getattr(obj, "y", 0))
            
            # Fallback for scroll events which might still use flat attributes
            if hasattr(e, "local_x"):
                return float(getattr(e, "local_x", 0)), float(getattr(e, "local_y", 0))
        
        return 0.0, 0.0

    def _on_pan_start(self, e):
        x, y = self._extract_coords(e, is_delta=False)
        
        wp = self.viewport.screen_to_world(Point(x, y))
        self.dragging_gate = None
        for gate in reversed(list(self.ui_gates.values())):
            if gate.contains(wp.x, wp.y):
                self.dragging_gate = gate
                break

    def _on_pan(self, e):
        dx, dy = self._extract_coords(e, is_delta=True)

        if self.dragging_gate:
            g = self.dragging_gate
            g._raw_world_x += dx / self.viewport.zoom
            g._raw_world_y += dy / self.viewport.zoom
            g.world_pos = self.viewport.snap_to_grid(Point(g._raw_world_x, g._raw_world_y))
        else:
            self.viewport.pan(dx, dy)
        self.update_all_components()

    def _on_pan_end(self, e):
        self.dragging_gate = None

    def _on_scroll(self, e):
        sdy = 0.0
        # Check for nested scroll_delta object
        if hasattr(e, "scroll_delta") and e.scroll_delta is not None:
            sdy = float(getattr(e.scroll_delta, "y", 0))
        # Legacy fallback
        elif hasattr(e, "scroll_delta_y"):
            sdy = float(getattr(e, "scroll_delta_y", 0))
            
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
                    self.grid_canvas.shapes.append(cv.Circle(sp.x, sp.y, max(1, 2*self.viewport.zoom), dot))

    def update_all_components(self) -> None:
        try:
            self.viewport.width = self.page.window.width
            self.viewport.height = self.page.window.height
        except: pass
        self._draw_grid()
        for gate in self.ui_gates.values():
            gate.update_render_position()
        self.view.update()
""",
    "app/ui/bridge.py": """from typing import Dict
from app.engine.simulation.controller import SimulationController
from app.ui.canvas.renderer import CanvasRenderer
from app.ui.components.gate_ui import UIGate
import uuid

class UIEngineBridge:
    def __init__(self, engine: SimulationController, renderer: CanvasRenderer):
        self.engine = engine
        self.renderer = renderer

    def spawn_gate(self, gate_type: str, world_x: float, world_y: float) -> None:
        gate_id = str(uuid.uuid4())
        ui_gate = UIGate(gate_id, world_x, world_y, label=gate_type.upper())
        self.renderer.add_gate(ui_gate)
""",
    "app/testing/test_viewport.py": """from app.ui.canvas.viewport import Viewport, Point

def test_viewport_pan():
    vp = Viewport(800, 600)
    vp.pan(100, 50)
    assert vp.camera.x == -100
    assert vp.camera.y == -50

def test_viewport_zoom():
    vp = Viewport(800, 600)
    vp.apply_zoom(2.0, 0, 0)
    assert vp.zoom == 2.0
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

    bridge.spawn_gate("AND", 100, 100)
    bridge.spawn_gate("OR", 300, 150)
    bridge.spawn_gate("NOT", 500, 200)

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

print("✅ Flet API Blueprint Applied. Native objects used for mouse events.")