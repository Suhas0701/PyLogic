import flet as ft

class ToolboxPanel:
    """Left sidebar for component selection."""
    def __init__(self, bridge):
        self.bridge = bridge
        self.active_btn = None
        self.active_tool_is_custom = False
        
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
        # Phase 10: Listen for new Custom ICs being packaged
        self.bridge.engine.on("library_updated", self._build_tools)

    def _build_tools(self):
        self.content.controls.clear()
        
        # UX: Sticky Tool Toggle
        self.sticky_toggle = ft.Checkbox(
            label="Sticky Tools", 
            value=False, 
            fill_color=getattr(ft.Colors, 'BLUE_700', 'blue700'), 
            label_style=ft.TextStyle(color=getattr(ft.Colors, 'WHITE_70', 'white70'), size=12)
        )

        controls = [
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
            self._make_tool("SPLITTER", ft.Icons.CALL_SPLIT),
            self._make_tool("MERGER", ft.Icons.MERGE_TYPE),
            self._make_tool("8-BIT SWITCH", ft.Icons.DATA_ARRAY),
            ft.Divider(color=getattr(ft.Colors, 'WHITE_24', 'white24')),
            
            ft.Text("SEQUENTIAL MEMORY", color=getattr(ft.Colors, 'WHITE_54', 'white54'), size=12, weight="bold"),
            self._make_tool("D_FF", ft.Icons.MEMORY),
            self._make_tool("T_FF", ft.Icons.MEMORY),
            self._make_tool("SR_LATCH", ft.Icons.MEMORY),
        ]
        
        # Phase 10: Inject Custom ICs dynamically at the bottom!
        if getattr(self.bridge, 'custom_ic_library', None) and len(self.bridge.custom_ic_library) > 0:
            controls.append(ft.Divider(color=getattr(ft.Colors, 'WHITE_24', 'white24')))
            controls.append(ft.Text("CUSTOM CHIPS", color=ft.Colors.AMBER_400, size=12, weight="bold"))
            for ic_name in self.bridge.custom_ic_library.keys():
                controls.append(self._make_tool(ic_name, ft.Icons.MEMORY, is_custom=True))

        self.content.controls.extend(controls)
        try: 
            self.view.update()
        except: 
            pass

    def _make_tool(self, name: str, icon: str, is_custom: bool = False):
        color = ft.Colors.AMBER_700 if is_custom else getattr(ft.Colors, 'BLUE_GREY_800', 'bluegrey800')
        
        btn = ft.ElevatedButton(
            name,
            icon=icon,
            width=160 if is_custom else 200, # Shrink slightly to fit the trash can
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=4),
                bgcolor=color,
                color=ft.Colors.WHITE
            ),
            on_click=lambda e, n=name: self._on_select(e.control, n)
        )
        
        # If it's a Custom IC, wrap it in a Row with a Delete button!
        if is_custom:
            return ft.Row([
                btn,
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=ft.Colors.RED_400,
                    tooltip="Delete Custom IC",
                    on_click=lambda e, n=name: self.bridge.delete_custom_ic(n)
                )
            ], spacing=2)
            
        return btn

    def _on_select(self, btn_control, name: str):
        # 1. Revert the old button to its original color
        if self.active_btn and self.bridge.active_tool:
            self.active_btn.style.bgcolor = ft.Colors.AMBER_700 if self.active_tool_is_custom else getattr(ft.Colors, 'BLUE_GREY_800', 'bluegrey800')
            self.active_btn.update()
            
        # 2. Toggle off if clicking the currently active tool
        if self.bridge.active_tool == name:
            self.bridge.active_tool = None
            self.active_btn = None
            self.active_tool_is_custom = False
            
        # 3. Toggle on if clicking a new tool
        else:
            self.bridge.active_tool = name
            self.active_btn = btn_control
            self.active_tool_is_custom = name in getattr(self.bridge, 'custom_ic_library', {})
            btn_control.style.bgcolor = getattr(ft.Colors, 'BLUE_700', 'blue700')
            btn_control.update()

    def _clear_tool(self):
        # Abort the deselection if the user enabled Sticky Tools!
        if getattr(self, 'sticky_toggle', None) and self.sticky_toggle.value:
            return

        if self.active_btn:
            self.active_btn.style.bgcolor = ft.Colors.AMBER_700 if self.active_tool_is_custom else getattr(ft.Colors, 'BLUE_GREY_800', 'bluegrey800')
            try: 
                self.active_btn.update()
            except: 
                pass
            self.active_btn = None
            self.active_tool_is_custom = False
            
        self.bridge.active_tool = None

class InspectorPanel:
    """Right sidebar for dynamic property editing."""
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
        except: 
            pass

    def _change_hz(self, e):
        self.bridge.set_clock_hz(e.control.value)