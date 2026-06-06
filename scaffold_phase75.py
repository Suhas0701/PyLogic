import os

files = {
    # --- 1. NEW UI PANELS (Toolbox & Inspector) ---
    "app/ui/panels.py": """import flet as ft

class ToolboxPanel:
    \"\"\"Left sidebar for component selection.\"\"\"
    def __init__(self, bridge):
        self.bridge = bridge
        self.active_btn = None
        
        self.content = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=5)
        self.view = ft.Container(
            width=220, bgcolor=ft.Colors.BLUE_GREY_900,
            border=getattr(ft, 'Border', ft.border).only(right=ft.border.BorderSide(2, ft.Colors.BLACK38)),
            padding=10,
            content=self.content
        )
        
        self._build_tools()

    def _build_tools(self):
        self.content.controls.extend([
            ft.Text("I/O COMPONENTS", color=ft.Colors.WHITE54, size=12, weight="bold"),
            self._make_tool("SWITCH", ft.Icons.TOGGLE_ON),
            self._make_tool("LED", ft.Icons.LIGHTBULB),
            self._make_tool("CLOCK", ft.Icons.ACCESS_TIME),
            ft.Divider(color=ft.Colors.WHITE24),
            
            ft.Text("LOGIC GATES", color=ft.Colors.WHITE54, size=12, weight="bold"),
            self._make_tool("AND", ft.Icons.ACCOUNT_TREE),
            self._make_tool("OR", ft.Icons.ACCOUNT_TREE_OUTLINED),
            self._make_tool("NOT", ft.Icons.CHANGE_HISTORY),
            ft.Divider(color=ft.Colors.WHITE24),
            
            ft.Text("SEQUENTIAL MEMORY", color=ft.Colors.WHITE54, size=12, weight="bold"),
            self._make_tool("D_FF", ft.Icons.MEMORY),
            self._make_tool("T_FF", ft.Icons.MEMORY),
            self._make_tool("SR_LATCH", ft.Icons.MEMORY),
        ])

    def _make_tool(self, name: str, icon: str):
        btn = ft.ElevatedButton(
            text=name,
            icon=icon,
            width=200,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=4),
                bgcolor=ft.Colors.BLUE_GREY_800,
                color=ft.Colors.WHITE
            ),
            on_click=lambda e, n=name: self._on_select(e.control, n)
        )
        return btn

    def _on_select(self, btn_control, name: str):
        # Reset previous button
        if self.active_btn:
            self.active_btn.style.bgcolor = ft.Colors.BLUE_GREY_800
            self.active_btn.update()
            
        # If clicking same tool, deselect
        if self.bridge.active_tool == name:
            self.bridge.active_tool = None
            self.active_btn = None
        else:
            self.bridge.active_tool = name
            self.active_btn = btn_control
            btn_control.style.bgcolor = ft.Colors.BLUE_700
            btn_control.update()


class InspectorPanel:
    \"\"\"Right sidebar for dynamic property editing.\"\"\"
    def __init__(self, bridge):
        self.bridge = bridge
        self.content = ft.Column(spacing=10)
        self.view = ft.Container(
            width=250, bgcolor=ft.Colors.BLUE_GREY_900,
            border=getattr(ft, 'Border', ft.border).only(left=ft.border.BorderSide(2, ft.Colors.BLACK38)),
            padding=15,
            content=self.content
        )
        
        # Subscribe to Bridge selection events
        self.bridge.engine.on("selection_changed", self.update_view)
        self.update_view()

    def update_view(self, ui_gate=None):
        self.content.controls.clear()
        
        if not ui_gate:
            self.content.controls.append(
                ft.Container(
                    content=ft.Text("No Component Selected", color=ft.Colors.WHITE54, text_align="center"),
                    expand=True, alignment=ft.Alignment(0, 0)
                )
            )
        else:
            self.content.controls.extend([
                ft.Text("PROPERTIES", weight="bold", color=ft.Colors.WHITE),
                ft.Divider(color=ft.Colors.WHITE24),
                ft.TextField(label="ID", value=ui_gate.gate_id, read_only=True, text_size=11),
                ft.TextField(label="Type", value=ui_gate.label, read_only=True),
            ])
            
            # Dynamic Properties based on component type
            if ui_gate.label == "CLOCK":
                hz_slider = ft.Slider(min=1, max=20, value=self.bridge.clock_hz, divisions=19, label="{value} Hz", on_change=self._change_hz)
                self.content.controls.extend([
                    ft.Text("Global Clock Frequency", size=12, color=ft.Colors.WHITE70),
                    hz_slider
                ])
                
            self.content.controls.extend([
                ft.Divider(color=ft.Colors.TRANSPARENT),
                ft.ElevatedButton(
                    "Delete Component", 
                    icon=ft.Icons.DELETE, 
                    bgcolor=ft.Colors.RED_900, 
                    color=ft.Colors.WHITE,
                    on_click=lambda e: self.bridge.delete_selected()
                )
            ])
            
        try:
            self.view.update()
        except: pass

    def _change_hz(self, e):
        self.bridge.set_clock_hz(e.control.value)
""",

    # --- 2. UPDATE BRIDGE (Placement, Selection, Deletion Logic) ---
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

class UIEngineBridge:
    def __init__(self, engine: SimulationController, renderer: CanvasRenderer):
        self.engine = engine
        self.renderer = renderer
        self.renderer.bind_bridge(self)
        
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
            self.engine.tick_clocks()

    def set_clock_hz(self, hz: float):
        self.clock_hz = max(0.1, float(hz))

    def _on_engine_stabilized(self):
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
        
        # Auto-select newly spawned gate
        self.select_component(ui_gate)

    def attempt_connection(self, out_uipin: UIPin, in_uipin: UIPin) -> None:
        try:
            backend_source = out_uipin.gate.backend_comp.outputs[out_uipin.pin_id]
            backend_target = in_uipin.gate.backend_comp.inputs[in_uipin.pin_id]
            
            Wire(backend_source, backend_target)
            self.engine.detect_loops()
            
            ui_wire = UIWire(out_uipin, in_uipin, backend_source)
            self.renderer.ui_wires.append(ui_wire)
            
            try:
                backend_target.set_state(backend_source.state)
            except AttributeError:
                pass
            self.engine.queue_evaluation(in_uipin.gate.backend_comp)
            self.engine.run_until_stable()
            
        except InvalidConnectionError as e:
            self.renderer.show_error(str(e))
        except CircuitLoopError as e:
            self.renderer.show_error(str(e))
            backend_target.connected_wire.disconnect()
            
        self.renderer.update_all_components()

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
            self.engine.run_until_stable()
            self.renderer.update_all_components()

    def delete_selected(self) -> None:
        \"\"\"Completely severs a component from UI and backend memory safely.\"\"\"
        if not self.selected_gate: return
        gate = self.selected_gate

        # 1. Sever all input wires
        for pin in gate.pins:
            if pin.is_input:
                self.remove_connection(pin)
            else:
                # 2. Sever all output wires
                wires_to_remove = [w for w in self.renderer.ui_wires if w.source_pin == pin]
                for w in wires_to_remove:
                    self.remove_connection(w.target_pin)

        # 3. Remove from UI dictionaries
        del self.renderer.ui_gates[gate.gate_id]
        self.renderer.gates_layer.controls.remove(gate.control)

        # 4. Remove from Backend Simulation
        if gate.backend_comp in self.engine.components:
            self.engine.components.remove(gate.backend_comp)
        if gate.backend_comp in self.engine.clocks:
            self.engine.clocks.remove(gate.backend_comp)

        # 5. Clear selection and re-render
        self.select_component(None)
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
            CircuitDeserializer.import_state(self, json_string)
        except ValueError as e:
            self.renderer.show_error(str(e))
""",

    # --- 3. UPDATE RENDERER (Keyboard Bindings & Tool Placement) ---
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
        
        # --- NEW: Bind Global Keyboard Events for Deletion ---
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

        self.toolbar = ft.Container(
            content=ft.Row([
                ft.IconButton(icon=ft.Icons.PLAY_ARROW, on_click=self._on_play, icon_color=ft.Colors.GREEN, tooltip="Play"),
                ft.IconButton(icon=ft.Icons.PAUSE, on_click=self._on_pause, icon_color=ft.Colors.AMBER, tooltip="Pause"),
                ft.IconButton(icon=ft.Icons.SKIP_NEXT, on_click=self._on_step, icon_color=ft.Colors.BLUE, tooltip="Step"),
                ft.Container(width=20),
                ft.VerticalDivider(width=10, color=ft.Colors.WHITE24),
                ft.IconButton(icon=ft.Icons.DOWNLOAD, on_click=self._on_save, icon_color=ft.Colors.WHITE, tooltip="Save JSON"),
                ft.IconButton(icon=ft.Icons.UPLOAD, on_click=self._on_load, icon_color=ft.Colors.WHITE, tooltip="Load JSON"),
                ft.IconButton(icon=ft.Icons.DELETE_SWEEP, on_click=self._on_clear, icon_color=ft.Colors.RED_400, tooltip="Clear Workspace"),
            ]),
            top=15, left=15, bgcolor=ft.Colors.BLUE_GREY_900, border_radius=8, padding=5,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK54)
        )
        self.root_stack.controls.append(self.toolbar)
        self.view = ft.Container(content=self.root_stack, expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE)

    def bind_bridge(self, bridge):
        self.bridge = bridge

    def _on_keyboard(self, e: ft.KeyboardEvent):
        # Allow deletion via Backspace or Delete key
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
                print(f"Project JSON:\\n{json_str}")
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
                # Select the gate we are dragging
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
        
        # 1. TOOL PLACEMENT LOGIC
        if self.bridge and self.bridge.active_tool:
            self.bridge.spawn_gate(self.bridge.active_tool, wp.x, wp.y)
            return

        # 2. SELECTION & INTERACTION LOGIC
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
            # Update selection visually
            gate.is_selected = (self.bridge and gate == self.bridge.selected_gate)
            gate.update_render_position()
        self.view.update()
""",

    # --- 4. UPDATE MAIN APP LAYOUT ---
    "main.py": """import flet as ft
from app.engine.simulation.controller import SimulationController
from app.ui.canvas.renderer import CanvasRenderer
from app.ui.bridge import UIEngineBridge
from app.ui.panels import ToolboxPanel, InspectorPanel

def main(page: ft.Page):
    page.title = "PyLogic Simulator"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK

    # Initialize Backend
    engine = SimulationController()
    
    # Initialize Core UI
    renderer = CanvasRenderer(page)
    bridge = UIEngineBridge(engine, renderer)
    
    # Initialize Sidebars
    toolbox = ToolboxPanel(bridge)
    inspector = InspectorPanel(bridge)
    
    # Construct Full Editor Layout
    layout = ft.Row(
        controls=[
            toolbox.view,
            renderer.view,
            inspector.view
        ],
        expand=True,
        spacing=0
    )

    page.add(layout)

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

print("✅ Phase 7.5 Deployed: Workspace Panels, Tool Placement, and Component Deletion active!")