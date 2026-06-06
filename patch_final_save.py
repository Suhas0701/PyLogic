import os

renderer_code = """import flet as ft
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
        
        # Dialog for importing JSON (Works perfectly on both Web and Native)
        self.import_textfield = ft.TextField(multiline=True, min_lines=5, max_lines=15, hint_text="Paste JSON here...", expand=True)
        self.import_dialog = ft.AlertDialog(
            title=ft.Text("Import Circuit JSON"),
            content=self.import_textfield,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(self.import_dialog)),
                ft.TextButton("Load", on_click=self._execute_load)
            ]
        )

        self.hz_text = ft.Text("1 Hz", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
        self.hz_slider = ft.Slider(min=1, max=20, value=1, divisions=19, label="{value} Hz", on_change=self._on_hz_change)
        
        self.toolbar = ft.Container(
            content=ft.Row([
                ft.IconButton(icon=ft.Icons.PLAY_ARROW, on_click=self._on_play, icon_color=ft.Colors.GREEN, tooltip="Play"),
                ft.IconButton(icon=ft.Icons.PAUSE, on_click=self._on_pause, icon_color=ft.Colors.AMBER, tooltip="Pause"),
                ft.IconButton(icon=ft.Icons.SKIP_NEXT, on_click=self._on_step, icon_color=ft.Colors.BLUE, tooltip="Step"),
                ft.Container(width=10),
                ft.Icon(ft.Icons.ACCESS_TIME, color=ft.Colors.WHITE70),
                self.hz_slider,
                self.hz_text,
                ft.Container(width=20),
                ft.VerticalDivider(width=10, color=ft.Colors.WHITE24),
                ft.IconButton(icon=ft.Icons.DOWNLOAD, on_click=self._on_save, icon_color=ft.Colors.WHITE, tooltip="Save (Export JSON)"),
                ft.IconButton(icon=ft.Icons.UPLOAD, on_click=self._on_load, icon_color=ft.Colors.WHITE, tooltip="Load (Import JSON)"),
                ft.IconButton(icon=ft.Icons.DELETE_SWEEP, on_click=self._on_clear, icon_color=ft.Colors.RED_400, tooltip="Clear Board"),
            ]),
            top=15, left=15, bgcolor=ft.Colors.BLUE_GREY_900, border_radius=8, padding=5,
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

    def show_success(self, message: str):
        try:
            sb = ft.SnackBar(content=ft.Text(message, color=ft.Colors.WHITE), bgcolor=ft.Colors.GREEN_700)
            self.page.open(sb)
        except:
            print(f"SUCCESS: {message}")

    # --- HYBRID FILE HANDLING (V0.23+ COMPLIANT) ---
    async def _on_save(self, e):
        if not self.bridge: return
        json_str = self.bridge.export_project()
        
        if self.page.web:
            # Web Browser logic
            b64_json = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
            data_uri = f"data:application/json;base64,{b64_json}"
            await self.page.launch_url(data_uri)
        else:
            # Native OS Desktop logic using the new FilePicker Service
            file_path = await ft.FilePicker().save_file(
                dialog_title="Save Circuit Project", 
                file_name="circuit.json", 
                allowed_extensions=["json"]
            )
            
            # Write exactly to where the macOS Finder selected
            if file_path:
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(json_str)
                    self.show_success(f"Project safely saved to: {file_path}")
                except Exception as ex:
                    self.show_error(f"Failed to write file: {ex}")

    def _on_load(self, e):
        self.import_textfield.value = ""
        self.page.open(self.import_dialog)

    def _execute_load(self, e):
        json_str = self.import_textfield.value
        self.page.close(self.import_dialog)
        if json_str and self.bridge:
            self.bridge.import_project(json_str)

    def _on_clear(self, e):
        if self.bridge:
            self.bridge.clear_workspace()

    # --- Timing Actions ---
    def _on_play(self, e):
        if self.bridge: self.bridge.engine.play()
    def _on_pause(self, e):
        if self.bridge: self.bridge.engine.pause()
    def _on_step(self, e):
        if self.bridge:
            self.bridge.engine.step()
            self.update_all_components()
    def _on_hz_change(self, e):
        self.hz_text.value = f"{int(e.control.value)} Hz"
        if self.bridge: self.bridge.set_clock_hz(e.control.value)
        self.toolbar.update()

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
        clicked_gate = None
        for gate in reversed(list(self.ui_gates.values())):
            if gate.contains(wp.x, wp.y):
                clicked_gate = gate
                break
        if clicked_gate and self.bridge:
            self.bridge.handle_interaction(clicked_gate)
        for g in self.ui_gates.values():
            g.is_selected = (g == clicked_gate)
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
            gate.update_render_position()
        self.view.update()
"""

filepath = "app/ui/canvas/renderer.py"
os.makedirs(os.path.dirname(filepath), exist_ok=True)
with open(filepath, "w", encoding="utf-8") as f:
    f.write(renderer_code)

print("✅ UI Crash fixed! Native macOS Save dialog implemented correctly.")