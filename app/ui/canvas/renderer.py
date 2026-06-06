import flet as ft
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
            try:
                import js # type: ignore
                
                # 1. Safely attach data to the browser's global window object
                js.window.temp_circuit_data = json_str
                
                # 2. Run pure JavaScript to create a Blob and force the download
                js.window.eval("""
                    const blob = new Blob([window.temp_circuit_data], {type: "application/json"});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.style.display = "none";
                    a.href = url;
                    a.download = "circuit.json";
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                    delete window.temp_circuit_data; // Cleanup memory
                """)
                
                print("✅ Web download triggered via HTML5 Blob!")
                
            except Exception as ex:
                # Print directly to the browser console so we can see any failures
                print(f"⚠️ Web download failed: {ex}")
                
        else:
            # --- DESKTOP LOGIC ---
            try:
                # Note: Ensure you have import flet as ft at the top of your file
                import flet as ft 
                file_path = await ft.FilePicker().save_file(dialog_title="Save", file_name="circuit.json")
                if file_path:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(json_str)
                    print(f"✅ Saved to desktop: {file_path}")
            except Exception as ex:
                print(f"⚠️ Desktop save failed: {ex}")

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
            self.bridge.engine.emit("clear_active_tool")
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
        return -margin <= sp.x <= self.viewport.width + margin and \
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
            # Web-safe dimension retrieval
            vw = getattr(self.page, "width", None)
            vh = getattr(self.page, "height", None)
            if not vw and hasattr(self.page, "window"): vw = self.page.window.width
            if not vh and hasattr(self.page, "window"): vh = self.page.window.height
            
            # Ensure they are never None
            self.viewport.width = vw or 800
            self.viewport.height = vh or 600
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
