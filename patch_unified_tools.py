import os

# --- 1. Completely rewrite panels.py for a clean, guaranteed state ---
panels_code = """import flet as ft

class ToolboxPanel:
    \"\"\"Left sidebar for component selection.\"\"\"
    def __init__(self, bridge):
        self.bridge = bridge
        self.active_btn = None
        
        self.content = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=5)
        self.view = ft.Container(
            width=220, bgcolor=ft.Colors.BLUE_GREY_900,
            border=getattr(ft, 'Border', ft.border).only(right=ft.border.BorderSide(2, getattr(ft.Colors, 'BLACK_38', 'black38'))),
            padding=10,
            content=self.content
        )
        
        self._build_tools()
        # Listen for the drop event triggered by the canvas
        self.bridge.engine.on("clear_active_tool", self._clear_tool)

    def _build_tools(self):
        # UX: Sticky Tool Toggle
        self.sticky_toggle = ft.Checkbox(
            label="Sticky Tools", 
            value=False, 
            fill_color=getattr(ft.Colors, 'BLUE_700', 'blue700'), 
            label_style=ft.TextStyle(color=getattr(ft.Colors, 'WHITE_70', 'white70'), size=12)
        )

        self.content.controls.extend([
            self.sticky_toggle,
            ft.Divider(color=getattr(ft.Colors, 'WHITE_24', 'white24')),
            ft.Text("I/O COMPONENTS", color=getattr(ft.Colors, 'WHITE_54', 'white54'), size=12, weight="bold"),
            self._make_tool("SWITCH", ft.Icons.TOGGLE_ON),
            self._make_tool("LED", ft.Icons.LIGHTBULB),
            self._make_tool("CLOCK", ft.Icons.ACCESS_TIME),
            ft.Divider(color=getattr(ft.Colors, 'WHITE_24', 'white24')),
            
            ft.Text("LOGIC GATES", color=getattr(ft.Colors, 'WHITE_54', 'white54'), size=12, weight="bold"),
            self._make_tool("AND", ft.Icons.ACCOUNT_TREE),
            self._make_tool("OR", ft.Icons.ACCOUNT_TREE_OUTLINED),
            self._make_tool("NOT", ft.Icons.CHANGE_HISTORY),
            ft.Divider(color=getattr(ft.Colors, 'WHITE_24', 'white24')),
            
            ft.Text("SEQUENTIAL MEMORY", color=getattr(ft.Colors, 'WHITE_54', 'white54'), size=12, weight="bold"),
            self._make_tool("D_FF", ft.Icons.MEMORY),
            self._make_tool("T_FF", ft.Icons.MEMORY),
            self._make_tool("SR_LATCH", ft.Icons.MEMORY),
        ])

    def _make_tool(self, name: str, icon: str):
        btn = ft.ElevatedButton(
            name,
            icon=icon,
            width=200,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=4),
                bgcolor=getattr(ft.Colors, 'BLUE_GREY_800', 'bluegrey800'),
                color=ft.Colors.WHITE
            ),
            on_click=lambda e, n=name: self._on_select(e.control, n)
        )
        return btn

    def _on_select(self, btn_control, name: str):
        if self.active_btn:
            self.active_btn.style.bgcolor = getattr(ft.Colors, 'BLUE_GREY_800', 'bluegrey800')
            self.active_btn.update()
            
        if self.bridge.active_tool == name:
            self.bridge.active_tool = None
            self.active_btn = None
        else:
            self.bridge.active_tool = name
            self.active_btn = btn_control
            btn_control.style.bgcolor = getattr(ft.Colors, 'BLUE_700', 'blue700')
            btn_control.update()

    def _clear_tool(self):
        # Abort the deselection if the user enabled Sticky Tools!
        if getattr(self, 'sticky_toggle', None) and self.sticky_toggle.value:
            return

        if self.active_btn:
            self.active_btn.style.bgcolor = getattr(ft.Colors, 'BLUE_GREY_800', 'bluegrey800')
            try: self.active_btn.update()
            except: pass
            self.active_btn = None
        self.bridge.active_tool = None

class InspectorPanel:
    \"\"\"Right sidebar for dynamic property editing.\"\"\"
    def __init__(self, bridge):
        self.bridge = bridge
        self.content = ft.Column(spacing=10)
        self.view = ft.Container(
            width=250, bgcolor=ft.Colors.BLUE_GREY_900,
            border=getattr(ft, 'Border', ft.border).only(left=ft.border.BorderSide(2, getattr(ft.Colors, 'BLACK_38', 'black38'))),
            padding=15,
            content=self.content
        )
        
        self.bridge.engine.on("selection_changed", self.update_view)
        self.update_view()

    def update_view(self, ui_gate=None):
        self.content.controls.clear()
        
        if not ui_gate:
            self.content.controls.append(
                ft.Container(
                    content=ft.Text("No Component Selected", color=getattr(ft.Colors, 'WHITE_54', 'white54'), text_align="center"),
                    expand=True, alignment=ft.Alignment(0, 0)
                )
            )
        else:
            self.content.controls.extend([
                ft.Text("PROPERTIES", weight="bold", color=ft.Colors.WHITE),
                ft.Divider(color=getattr(ft.Colors, 'WHITE_24', 'white24')),
                ft.TextField(label="ID", value=ui_gate.gate_id, read_only=True, text_size=11),
                ft.TextField(label="Type", value=ui_gate.label, read_only=True),
            ])
            
            if ui_gate.label == "CLOCK":
                hz_slider = ft.Slider(min=1, max=20, value=self.bridge.clock_hz, divisions=19, label="{value} Hz", on_change=self._change_hz)
                self.content.controls.extend([
                    ft.Text("Global Clock Frequency", size=12, color=getattr(ft.Colors, 'WHITE_70', 'white70')),
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
"""

filepath_panels = "app/ui/panels.py"
os.makedirs(os.path.dirname(filepath_panels), exist_ok=True)
with open(filepath_panels, "w", encoding="utf-8") as f:
    f.write(panels_code)
print("✅ Toolbox Panel completely rebuilt with Checkbox and Single-Shot logic.")


# --- 2. Patch the Renderer to trigger the deselect event ---
filepath_renderer = "app/ui/canvas/renderer.py"
try:
    with open(filepath_renderer, "r", encoding="utf-8") as f:
        code_renderer = f.read()

    # We look for the spawn gate command in the _on_tap function
    old_tap = """        if self.bridge and self.bridge.active_tool:
            self.bridge.spawn_gate(self.bridge.active_tool, wp.x, wp.y)
            return"""

    new_tap = """        if self.bridge and self.bridge.active_tool:
            self.bridge.spawn_gate(self.bridge.active_tool, wp.x, wp.y)
            self.bridge.engine.emit("clear_active_tool")
            return"""

    if old_tap in code_renderer:
        with open(filepath_renderer, "w", encoding="utf-8") as f:
            f.write(code_renderer.replace(old_tap, new_tap))
        print("✅ Renderer patched: Canvas will now command the Toolbox to deselect the tool.")
    elif "clear_active_tool" in code_renderer:
        print("✅ Renderer is already firing the deselect event.")
    else:
        print("⚠️ Could not find the _on_tap insertion point in renderer.py.")

except FileNotFoundError:
    print(f"Error: Could not find {filepath_renderer}")