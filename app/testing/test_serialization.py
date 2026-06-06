import pytest
import json
import flet as ft
import flet.canvas as cv
from app.engine.simulation.controller import SimulationController
from app.ui.canvas.renderer import CanvasRenderer
from app.ui.bridge import UIEngineBridge

class MockPage:
    def __init__(self):
        self.overlay = []
        self.web = False
    def run_task(self, task): pass
    def update(self): pass

# FIXED: Monkeypatch Flet updates to safely pass in Headless UI Tests
cv.Canvas.update = lambda self: None
ft.Container.update = lambda self: None
ft.Stack.update = lambda self: None

def test_serialization_roundtrip():
    page = MockPage()
    engine = SimulationController()
    renderer = CanvasRenderer(page)
    bridge = UIEngineBridge(engine, renderer)
    
    bridge.spawn_gate("SWITCH", 0, 0)
    bridge.spawn_gate("NOT", 100, 0)
    
    sw_ui = list(renderer.ui_gates.values())[0]
    not_ui = list(renderer.ui_gates.values())[1]
    
    bridge.attempt_connection(sw_ui.pins[0], not_ui.pins[0])
    
    json_str = bridge.export_project()
    data = json.loads(json_str)
    
    assert len(data["components"]) == 2
    assert len(data["wires"]) == 1
    
    bridge.clear_workspace()
    assert len(renderer.ui_gates) == 0
    
    bridge.import_project(json_str)
    
    assert len(renderer.ui_gates) == 2
    assert len(renderer.ui_wires) == 1
