import os

filepath_panels = "app/ui/panels.py"

try:
    with open(filepath_panels, "r", encoding="utf-8") as f:
        code_panels = f.read()

    # --- 1. Inject the UI Checkbox into the Toolbox ---
    old_build_tools = """        self.content.controls.extend([
            ft.Text("I/O COMPONENTS","""

    new_build_tools = """        # UX: Sticky Tool Toggle
        self.sticky_toggle = ft.Checkbox(
            label="Sticky Tools", 
            value=False, 
            fill_color=ft.Colors.BLUE_700, 
            label_style=ft.TextStyle(color=ft.Colors.WHITE_70, size=12)
        )

        self.content.controls.extend([
            self.sticky_toggle,
            ft.Divider(color=ft.Colors.WHITE_24),
            ft.Text("I/O COMPONENTS","""

    # --- 2. Intercept the deselect command ---
    old_clear_tool = """    def _clear_tool(self):
        if self.active_btn:"""

    new_clear_tool = """    def _clear_tool(self):
        # Abort the deselection if the user enabled Sticky Tools!
        if getattr(self, 'sticky_toggle', None) and self.sticky_toggle.value:
            return

        if self.active_btn:"""

    patched = False
    
    if old_build_tools in code_panels and "self.sticky_toggle" not in code_panels:
        code_panels = code_panels.replace(old_build_tools, new_build_tools)
        patched = True
        
    if old_clear_tool in code_panels and "self.sticky_toggle.value" not in code_panels:
        code_panels = code_panels.replace(old_clear_tool, new_clear_tool)
        patched = True

    if patched:
        with open(filepath_panels, "w", encoding="utf-8") as f:
            f.write(code_panels)
        print("✅ Toolbox Patched! Optional Sticky Tools toggle successfully added.")
    else:
        print("⚠️ Code already patched or insertion points not found.")

except FileNotFoundError:
    print(f"Error: Could not find {filepath_panels}")