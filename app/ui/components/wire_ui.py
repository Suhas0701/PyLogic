from ..canvas.viewport import Point
from .pin_ui import UIPin
import flet as ft
from app.engine.types import LogicState

class UIWire:
    def __init__(self, source_pin: UIPin, target_pin: UIPin, backend_source_pin):
        self.source_pin = source_pin
        self.target_pin = target_pin
        self.backend_source_pin = backend_source_pin # Link to Engine for live state polling

    def get_color(self) -> str:
        state = self.backend_source_pin.state
        if state == LogicState.HIGH:
            return ft.Colors.GREEN_400
        elif state == LogicState.LOW:
            return ft.Colors.GREEN_900
        else:
            return ft.Colors.AMBER_600 # UNDEFINED or HIGH_Z
