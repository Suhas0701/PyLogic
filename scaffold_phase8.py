import os

files = {
    # --- 1. NEW: PROFILING & DIAGNOSTICS ---
    "app/engine/profiler.py": """import time
from typing import Dict

class EngineProfiler:
    \"\"\"Tracks performance metrics for the simulation engine and UI rendering.\"\"\"
    def __init__(self):
        self.metrics: Dict[str, float] = {
            "last_engine_tick_ms": 0.0,
            "last_render_ms": 0.0,
            "total_components": 0,
            "culled_objects": 0
        }
        self._timers = {}

    def start(self, name: str):
        self._timers[name] = time.perf_counter()

    def stop(self, name: str):
        if name in self._timers:
            elapsed_ms = (time.perf_counter() - self._timers[name]) * 1000
            self.metrics[name] = elapsed_ms
            
    def get_summary(self) -> str:
        return (f"Engine: {self.metrics['last_engine_tick_ms']:.1f}ms | "
                f"Render: {self.metrics['last_render_ms']:.1f}ms | "
                f"Culled: {self.metrics.get('culled_objects', 0)}")
""",

    # --- 2. OPTIMIZED: ROUTING MEMOIZATION ---
    "app/ui/canvas/routing.py": """import math
from typing import List
from .viewport import Point

class OrthogonalRouter:
    _route_cache = {}

    @classmethod
    def route(cls, start: Point, end: Point, stub: float = 20.0) -> List[Point]:
        # PERFORMANCE: O(1) Cache lookup for static wires
        cache_key = (start.x, start.y, end.x, end.y, stub)
        if cache_key in cls._route_cache:
            return cls._route_cache[cache_key]

        path = [start]
        
        # Calculate standard orthogonal paths
        if start.x + stub < end.x - stub:
            mid_x = (start.x + end.x) / 2
            path.append(Point(mid_x, start.y))
            path.append(Point(mid_x, end.y))
        else:
            path.append(Point(start.x + stub, start.y))
            mid_y = (start.y + end.y) / 2
            path.append(Point(start.x + stub, mid_y))
            path.append(Point(end.x - stub, mid_y))
            path.append(Point(end.x - stub, end.y))
            
        path.append(end)
        
        # Bound cache size to prevent memory leaks in massive sessions
        if len(cls._route_cache) > 5000:
            cls._route_cache.clear()
            
        cls._route_cache[cache_key] = path
        return path
""",

    # --- 3. OPTIMIZED: VIEWPORT CULLING & RENDERER ---
    "app/ui/canvas/renderer.py": """import flet as ft
import flet.canvas as cv
import base64
from typing import Dict, List, Optional
from .viewport import Viewport, Point
from .routing import OrthogonalRouter
from ..components.gate_ui import UIGate
from ..components.pin_ui import UIPin
from ..components.wire_ui import UIWire

class CanvasRenderer:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.on_keyboard_event = self._on_keyboard
        
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
        
        self.root_stack = ft.Stack(expand=True)
        self.root_stack.controls.append(ft.Container(bgcolor=ft.Colors.GREY_900, expand=True))
        
        self.grid_canvas = cv.Canvas(expand=True)
        self.root_stack.controls.append(self.grid_canvas)
        self.wire_canvas = cv.Canvas(expand=True)
        self.root_stack.controls.append(self.wire_canvas)
        self.gates_layer = ft.Stack(expand=True)
        self.root_stack.controls.append(self.gates_layer)
        
        self.glass_pane = ft.GestureDetector(
            on_pan_start=self._on_pan_start, on_pan_update=self._on_pan,
            on_pan_end=self._on_pan_end, on_scroll=self._on_scroll,
            on_tap=self._on_tap, on_secondary_tap_down=self._on_right_click,
            drag_interval=5,
            content=ft.Container(bgcolor="#01000000", expand=True)
        )
        self.root_stack.controls.append(self.glass_pane)
        
        self.import_textfield = ft.TextField(multiline=True, min_lines=5, max_lines=15, hint_text="Paste JSON here...", expand=True)
        self.import_dialog = ft.AlertDialog(
            title=ft.Text("Import Circuit JSON"),
            content=self.import_textfield,
            actions=[
                ft.TextButton("Cancel", on_click=self._close_dialog),
                ft.TextButton("Load", on_click=self._execute_load)
            ]
        )

        self.hz_text = ft.Text("1 Hz", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
        self.hz_slider = ft.Slider(min=1, max=20, value=1, divisions=19, label="{value} Hz", on_change=self._on_hz_change)
        
        # PERFORMANCE: Profiler UI Readout
        self.profiler_text = ft.Text("Ready", color=ft.Colors.GREEN_400, size=11, font_family="monospace")

        self.toolbar = ft.Container(
            content=ft.Row([
                ft.IconButton(icon=ft.Icons.PLAY_ARROW, on_click=self._on_play, icon_color=ft.Colors.GREEN, tooltip="Play"),
                ft.IconButton(icon=ft.Icons.PAUSE, on_click=self._on_pause, icon_color=ft.Colors.AMBER, tooltip="Pause"),
                ft.IconButton(icon=ft.Icons.SKIP_NEXT, on_click=self._on_step, icon_color=ft.Colors.BLUE, tooltip="Step"),
                ft.Container(width=10),
                ft.Icon(ft.Icons.ACCESS_TIME, color=ft.Colors.WHITE_70),
                self.hz_slider,
                self.hz_text,
                ft.Container(width=20),
                ft.VerticalDivider(width=10, color=ft.Colors.WHITE_24),
                ft.IconButton(icon=ft.Icons.DOWNLOAD, on_click=self._on_save, icon_color=ft.Colors.WHITE, tooltip="Save JSON"),
                ft.IconButton(icon=ft.Icons.UPLOAD, on_click=self._on_load, icon_color=ft.Colors.WHITE, tooltip="Load JSON"),
                ft.IconButton(icon=ft.Icons.DELETE_SWEEP, on_click=self._on_clear, icon_color=ft.Colors.RED_400, tooltip="Clear Workspace"),
                ft.Container(width=20),
                self.profiler_text
            ]),
            top=15, left=15, bgcolor=ft.Colors.BLUE_GREY_900, border_radius=8, padding=5,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK_54)
        )
        self.root_stack.controls.append(self.toolbar)
        self.view = ft.Container(content=self.root_stack, expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE)

    def bind_bridge(self, bridge):
        self.bridge = bridge

    def _on_keyboard(self, e: ft.KeyboardEvent):
        if e.key in ["Delete", "Backspace"] and self.bridge:
            self.bridge.delete_selected()

    def show_error(self, message: str):
        try:
            sb = ft.SnackBar(content=ft.Text(message, color=ft.Colors.WHITE), bgcolor=ft.Colors.RED_800)
            self.page.snack_bar = sb
            sb.open = True
            self.page.update()
        except: print(f"SIMULATION ERROR: {message}")

    def show_success(self, message: str):
        try:
            sb = ft.SnackBar(content=ft.Text(message, color=ft.Colors.WHITE), bgcolor=ft.Colors.GREEN_700)
            self.page.snack_bar = sb
            sb.open = True
            self.page.update()
        except: print(f"SUCCESS: {message}")

    def _close_dialog(self, e):
        self.import_dialog.open = False
        self.page.update()

    async def _on_save(self, e):
        if not self.bridge: return
        json_str = self.bridge.export_project()
        if self.page.web:
            b64_json = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
            data_uri = f"data:application/json;base64,{b64_json}"
            await self.page.launch_url(data_uri)
        else:
            try:
                file_path = await ft.FilePicker().save_file(dialog_title="Save", file_name="circuit.json")
                if file_path:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(json_str)
                    self.show_success(f"Saved: {file_path}")
            except Exception as ex:
                self.show_error(f"Save failed: {ex}")

    def _on_load(self, e):
        self.import_textfield.value = ""
        if self.import_dialog not in self.page.overlay:
            self.page.overlay.append(self.import_dialog)
        self.import_dialog.open = True
        self.page.update()

    def _execute_load(self, e):
        json_str = self.import_textfield.value
        self.import_dialog.open = False
        self.page.update()
        if json_str and self.bridge:
            self.bridge.import_project(json_str)

    def _on_clear(self, e):
        if self.bridge: self.bridge.clear_workspace()
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
        
        # PERFORMANCE: Only update if not batching
        if self.bridge and not self.bridge.is_batching:
            self.update_all_components()

    def _hit_test_pins(self, wp: Point) -> Optional[UIPin]:
        hit_radius = 20.0 / self.viewport.zoom
        closest_pin = None
        min_dist_sq = hit_radius**2
        for gate in self.ui_gates.values():
            if not gate.control.visible: continue # Skip hit testing off-screen gates
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
                if self.bridge: self.bridge.select_component(gate)
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
            if target_pin and target_pin.is_input != self.wiring_start_pin.is_input:
                out_pin = self.wiring_start_pin if not self.wiring_start_pin.is_input else target_pin
                in_pin = target_pin if target_pin.is_input else self.wiring_start_pin
                if self.bridge: self.bridge.attempt_connection(out_pin, in_pin)
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
        
        if self.bridge and self.bridge.active_tool:
            self.bridge.spawn_gate(self.bridge.active_tool, wp.x, wp.y)
            return

        clicked_gate = None
        for gate in reversed(list(self.ui_gates.values())):
            if gate.contains(wp.x, wp.y):
                clicked_gate = gate
                break
                
        if self.bridge:
            self.bridge.select_component(clicked_gate)
            if clicked_gate:
                self.bridge.handle_interaction(clicked_gate)
                
        self.update_all_components()
        
    def _on_right_click(self, e):
        x, y = self._extract_coords(e, is_delta=False)
        wp = self.viewport.screen_to_world(Point(x, y))
        hit_pin = self._hit_test_pins(wp)
        if hit_pin and hit_pin.is_input and self.bridge:
            self.bridge.remove_connection(hit_pin)

    # --- PERFORMANCE: Viewport Culling Checks ---
    def _is_in_viewport(self, sp: Point, margin: float = 100) -> bool:
        return -margin <= sp.x <= self.viewport.width + margin and \\
               -margin <= sp.y <= self.viewport.height + margin

    def _draw_grid(self):
        self.grid_canvas.shapes.clear()
        origin = self.viewport.world_to_screen(Point(0, 0))
        cross = ft.Paint(color=ft.Colors.GREEN_700, stroke_width=2)
        
        # Only draw origin cross if visible
        if self._is_in_viewport(origin):
            self.grid_canvas.shapes.append(cv.Line(origin.x-20, origin.y, origin.x+20, origin.y, cross))
            self.grid_canvas.shapes.append(cv.Line(origin.x, origin.y-20, origin.x, origin.y+20, cross))
            
        dot = ft.Paint(color=ft.Colors.WHITE_24, style=ft.PaintingStyle.FILL)
        
        # Determine strict bounds for grid loop to avoid 1600+ iterations
        start_x = int(self.viewport.screen_to_world(Point(0, 0)).x // 100) * 100
        end_x = int(self.viewport.screen_to_world(Point(self.viewport.width, 0)).x // 100) * 100 + 100
        start_y = int(self.viewport.screen_to_world(Point(0, 0)).y // 100) * 100
        end_y = int(self.viewport.screen_to_world(Point(0, self.viewport.height)).y // 100) * 100 + 100

        for x in range(start_x, end_x, 100):
            for y in range(start_y, end_y, 100):
                if x == 0 and y == 0: continue
                sp = self.viewport.world_to_screen(Point(x, y))
                self.grid_canvas.shapes.append(cv.Circle(sp.x, sp.y, max(1, 1.5 * self.viewport.zoom), dot))
        self.grid_canvas.update()

    def _draw_wires_and_pins(self):
        self.wire_canvas.shapes.clear()
        z = self.viewport.zoom
        culled_count = 0
        
        for uw in self.ui_wires:
            # CULLING: Skip wires if both start and end are far offscreen
            sp_start = self.viewport.world_to_screen(uw.source_pin.global_pos)
            sp_end = self.viewport.world_to_screen(uw.target_pin.global_pos)
            
            if not self._is_in_viewport(sp_start, 500) and not self._is_in_viewport(sp_end, 500):
                culled_count += 1
                continue
                
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
            # CULLING: DOM node visibility toggle
            sp_gate = self.viewport.world_to_screen(gate.world_pos)
            is_visible = self._is_in_viewport(sp_gate, 300)
            
            if gate.control.visible != is_visible:
                gate.control.visible = is_visible
                
            if not is_visible:
                culled_count += 1
                continue
                
            for pin in gate.pins:
                sp = self.viewport.world_to_screen(pin.global_pos)
                paint = pin_paint_in if pin.is_input else pin_paint_out
                self.wire_canvas.shapes.append(cv.Circle(sp.x, sp.y, pin.radius * z, paint))
                
        self.wire_canvas.update()
        
        # Update Profiler Readout
        if self.bridge and self.bridge.profiler:
            self.bridge.profiler.metrics["culled_objects"] = culled_count
            self.profiler_text.value = self.bridge.profiler.get_summary()

    def update_all_components(self) -> None:
        if not getattr(self, 'grid_canvas', None) or not self.grid_canvas.page:
            return
            
        if self.bridge and self.bridge.profiler:
            self.bridge.profiler.start("last_render_ms")
            
        try:
            self.viewport.width = self.page.window.width
            self.viewport.height = self.page.window.height
        except: pass
        
        is_dragging = self.wiring_start_pin is not None or self.dragging_gate is not None
        if not is_dragging:
            self._draw_grid() 
            
        self._draw_wires_and_pins()
        
        for gate in self.ui_gates.values():
            if gate.control.visible:
                gate.is_selected = (self.bridge and gate == self.bridge.selected_gate)
                gate.update_render_position()
                
        if self.bridge and self.bridge.profiler:
            self.bridge.profiler.stop("last_render_ms")
            
        self.view.update()
""",

    # --- 4. OPTIMIZED: BATCHING IN BRIDGE ---
    "app/ui/bridge.py": """import asyncio
import uuid
from typing import Dict, Optional
from app.engine.types import LogicState
from app.engine.simulation.controller import SimulationController
from app.engine.components.gates import ANDGate, ORGate, NOTGate
from app.engine.components.io import ToggleSwitch, LED
from app.engine.components.sequential import ClockGenerator, DFlipFlop, TFlipFlop, SRLatch
from app.engine.wire import Wire
from app.engine.exceptions import InvalidConnectionError, CircuitLoopError
from app.ui.canvas.renderer import CanvasRenderer
from app.ui.components.gate_ui import UIGate
from app.ui.components.pin_ui import UIPin
from app.ui.components.wire_ui import UIWire
from app.engine.serialization import CircuitSerializer, CircuitDeserializer

# PERFORMANCE: Import Profiler
from app.engine.profiler import EngineProfiler

class UIEngineBridge:
    def __init__(self, engine: SimulationController, renderer: CanvasRenderer):
        self.engine = engine
        self.renderer = renderer
        self.renderer.bind_bridge(self)
        
        self.profiler = EngineProfiler()
        self.is_batching = False # Prevents cascading UI renders
        
        self.engine.on("state_stabilized", self._on_engine_stabilized)
        self.engine.on("error", self._on_engine_error)
        
        self.gate_types = {
            "AND": ANDGate, "OR": ORGate, "NOT": NOTGate,
            "SWITCH": ToggleSwitch, "LED": LED,
            "CLOCK": ClockGenerator, "D_FF": DFlipFlop, "T_FF": TFlipFlop, "SR_LATCH": SRLatch
        }
        
        self.clock_hz = 1.0
        self.active_tool: Optional[str] = None
        self.selected_gate: Optional[UIGate] = None
        
        self.renderer.page.run_task(self._async_clock_loop)

    async def _async_clock_loop(self):
        while True:
            await asyncio.sleep(1.0 / self.clock_hz)
            if not self.is_batching:
                self.profiler.start("last_engine_tick_ms")
                self.engine.tick_clocks()
                self.profiler.stop("last_engine_tick_ms")

    def set_clock_hz(self, hz: float):
        self.clock_hz = max(0.1, float(hz))

    def _on_engine_stabilized(self):
        if not self.is_batching:
            self.renderer.update_all_components()

    def _on_engine_error(self, message: str):
        self.renderer.show_error(message)

    def select_component(self, ui_gate: Optional[UIGate]):
        self.selected_gate = ui_gate
        self.engine.emit("selection_changed", ui_gate)

    def spawn_gate(self, gate_type: str, world_x: float, world_y: float, force_id: Optional[str] = None) -> None:
        gate_id = force_id if force_id else str(uuid.uuid4())
        backend_gate = self.gate_types[gate_type.upper()](gate_id)
        self.engine.add_component(backend_gate)
        ui_gate = UIGate(gate_id, world_x, world_y, label=gate_type.upper(), backend_comp=backend_gate)
        self.renderer.add_gate(ui_gate)
        if not self.is_batching:
            self.select_component(ui_gate)

    def attempt_connection(self, out_uipin: UIPin, in_uipin: UIPin) -> None:
        try:
            backend_source = out_uipin.gate.backend_comp.outputs[out_uipin.pin_id]
            backend_target = in_uipin.gate.backend_comp.inputs[in_uipin.pin_id]
            Wire(backend_source, backend_target)
            self.engine.detect_loops()
            ui_wire = UIWire(out_uipin, in_uipin, backend_source)
            self.renderer.ui_wires.append(ui_wire)
            
            try: backend_target.set_state(backend_source.state)
            except AttributeError: pass
            
            self.engine.queue_evaluation(in_uipin.gate.backend_comp)
            
            if not self.is_batching:
                self.engine.run_until_stable()
                self.renderer.update_all_components()
                
        except InvalidConnectionError as e:
            self.renderer.show_error(str(e))
        except CircuitLoopError as e:
            self.renderer.show_error(str(e))
            backend_target.connected_wire.disconnect()

    def remove_connection(self, in_uipin: UIPin) -> None:
        wire_to_remove = next((w for w in self.renderer.ui_wires if w.target_pin == in_uipin), None)
        if wire_to_remove:
            self.renderer.ui_wires.remove(wire_to_remove)
            backend_target = in_uipin.gate.backend_comp.inputs[in_uipin.pin_id]
            backend_wire = backend_target.connected_wire

            if backend_wire:
                if backend_wire in backend_wire.source.connected_wires:
                    backend_wire.source.connected_wires.remove(backend_wire)
                backend_target.connected_wire = None
                backend_target.state = LogicState.LOW

            self.engine.queue_evaluation(in_uipin.gate.backend_comp)
            if not self.is_batching:
                self.engine.run_until_stable()
                self.renderer.update_all_components()

    def delete_selected(self) -> None:
        if not self.selected_gate: return
        gate = self.selected_gate

        for pin in gate.pins:
            if pin.is_input: self.remove_connection(pin)
            else:
                wires_to_remove = [w for w in self.renderer.ui_wires if w.source_pin == pin]
                for w in wires_to_remove: self.remove_connection(w.target_pin)

        del self.renderer.ui_gates[gate.gate_id]
        self.renderer.gates_layer.controls.remove(gate.control)

        if gate.backend_comp in self.engine.components:
            self.engine.components.remove(gate.backend_comp)
        if gate.backend_comp in self.engine.clocks:
            self.engine.clocks.remove(gate.backend_comp)

        self.select_component(None)
        if not self.is_batching:
            self.engine.run_until_stable()
            self.renderer.update_all_components()

    def handle_interaction(self, ui_gate: UIGate) -> None:
        if isinstance(ui_gate.backend_comp, ToggleSwitch):
            ui_gate.backend_comp.toggle()
            self.engine.run_until_stable()
            self.renderer.update_all_components()

    def clear_workspace(self) -> None:
        self.select_component(None)
        self.engine.components.clear()
        self.engine.clocks.clear()
        self.engine._eval_queue.clear()
        self.engine._in_queue.clear()
        self.renderer.ui_gates.clear()
        self.renderer.ui_wires.clear()
        self.renderer.gates_layer.controls.clear()
        self.renderer.wire_canvas.shapes.clear()
        self.renderer.update_all_components()

    def export_project(self) -> str:
        return CircuitSerializer.export_state(self)

    def import_project(self, json_string: str) -> None:
        try:
            # PERFORMANCE: Suppress UI renders while loading large JSON
            self.is_batching = True
            CircuitDeserializer.import_state(self, json_string)
        except ValueError as e:
            self.renderer.show_error(str(e))
        finally:
            self.is_batching = False
            self.engine.run_until_stable()
            self.renderer.update_all_components()
"""
}

for filepath, content in files.items():
    directory = os.path.dirname(filepath)
    if directory: os.makedirs(directory, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ Phase 8 Deployed: Viewport Culling, Event Batching, Router Caching, and Profiler installed!")