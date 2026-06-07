from ..canvas.viewport import Point
from .pin_ui import UIPin
import flet as ft

class UIWire:
    def __init__(self, source_pin: UIPin, target_pin: UIPin, backend_source_pin):
        self.source_pin = source_pin
        self.target_pin = target_pin
        self.backend_source_pin = backend_source_pin 

    def get_color(self) -> str:
        state = getattr(self.backend_source_pin, 'state', 0)
        if state > 0:
            return ft.Colors.GREEN_400
        else:
            return ft.Colors.GREEN_900