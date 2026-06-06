import flet as ft
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
        
        # Dynamic resizing based on pin count
        in_c, out_c = len(backend_comp.inputs), len(backend_comp.outputs)
        self.width = 80
        self.height = max(40, max(in_c, out_c) * 20 + 20)
        self.is_selected = False
        
        self.pins: List[UIPin] = []
        for i, pin_id in enumerate(backend_comp.inputs.keys()):
            y_offset = (self.height / (in_c + 1)) * (i + 1)
            self.pins.append(UIPin(self, pin_id, True, 0, y_offset))
            
        for i, pin_id in enumerate(backend_comp.outputs.keys()):
            y_offset = (self.height / (out_c + 1)) * (i + 1)
            self.pins.append(UIPin(self, pin_id, False, self.width, y_offset))

        # Include pin labels for complex gates
        stack_controls = [
            ft.Container(
                bgcolor=ft.Colors.BLUE_GREY_800, border_radius=5, expand=True,
                alignment=ft.Alignment(0, 0),
                content=ft.Text(self.label, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
            )
        ]
        
        # Draw pin names inside the gate
        for pin in self.pins:
            align_x = -0.8 if pin.is_input else 0.8
            stack_controls.append(ft.Container(
                alignment=ft.Alignment(align_x, -1 + (pin.rel_y / self.height) * 2),
                content=ft.Text(pin.pin_id, size=10, color=ft.Colors.WHITE_54, weight=ft.FontWeight.W_600)
            ))

        self.control = ft.Container(
            width=self.width, height=self.height,
            border=getattr(ft, 'Border', ft.border).all(2, ft.Colors.TRANSPARENT),
            content=ft.Stack(controls=stack_controls, expand=True),
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
        bg = ft.Colors.BLUE_GREY_800
        shadow = None
        if self.label in ["SWITCH", "CLOCK"]:
            state_obj = getattr(self.backend_comp, "_state", None)
            # Safely parse the Enum so the box flashes properly
            is_on = str(state_obj).endswith("HIGH") or state_obj == 1
            bg = ft.Colors.GREEN_600 if is_on else ft.Colors.RED_900
        elif self.label == "LED":
            is_lit = getattr(self.backend_comp, "is_lit", False)
            bg = ft.Colors.RED_400 if is_lit else ft.Colors.BLUE_GREY_900
            if is_lit: shadow = ft.BoxShadow(spread_radius=10, blur_radius=20, color=ft.Colors.RED_ACCENT_400)
        
        # The background container is the first element in the stack
        self.control.content.controls[0].bgcolor = bg
        self.control.content.controls[0].shadow = shadow

    def update_render_position(self) -> None:
        if not self.viewport: return
        self._update_visual_state()
        sp = self.viewport.world_to_screen(self.world_pos)
        self.control.left = sp.x
        self.control.top = sp.y
        self.control.width = self.width * self.viewport.zoom
        self.control.height = self.height * self.viewport.zoom
        border_color = ft.Colors.AMBER_400 if self.is_selected else ft.Colors.TRANSPARENT
        self.control.border = getattr(ft, 'Border', ft.border).all(2 * self.viewport.zoom, border_color)
