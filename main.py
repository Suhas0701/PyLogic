import flet as ft
import traceback
from app.engine.simulation.controller import SimulationController
from app.ui.canvas.renderer import CanvasRenderer
from app.ui.bridge import UIEngineBridge
from app.ui.panels import ToolboxPanel, InspectorPanel

def main(page: ft.Page):
    page.title = "PyLogic Simulator"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK
    
    # PRODUCTION HARDENING: Global Error Boundary
    def on_global_error(e):
        print(f"Unhandled Exception: {e.data}")
        # Extract meaningful message for the user
        error_msg = str(e.data).split("\n")[-2] if "\n" in str(e.data) else str(e.data)
        sb = ft.SnackBar(content=ft.Text(f"Crash Prevented: {error_msg}", color=ft.Colors.WHITE), bgcolor=ft.Colors.RED_900)
        page.snack_bar = sb
        sb.open = True
        page.update()
        
    page.on_error = on_global_error

    # Initialize Core Systems
    engine = SimulationController()
    renderer = CanvasRenderer(page)
    bridge = UIEngineBridge(engine, renderer)
    
    # Initialize UI Panels
    toolbox = ToolboxPanel(bridge)
    inspector = InspectorPanel(bridge)
    
    # Construct Application Layout
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
