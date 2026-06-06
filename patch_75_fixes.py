import os

# --- 1. Fix the Flet ElevatedButton Syntax ---
filepath_panels = "app/ui/panels.py"
try:
    with open(filepath_panels, "r", encoding="utf-8") as f:
        code_panels = f.read()

    # Change keyword 'text=name' to positional 'name'
    old_btn = """        btn = ft.ElevatedButton(
            text=name,
            icon=icon,"""
    
    new_btn = """        btn = ft.ElevatedButton(
            name,
            icon=icon,"""

    if old_btn in code_panels:
        with open(filepath_panels, "w", encoding="utf-8") as f:
            f.write(code_panels.replace(old_btn, new_btn))
        print("✅ Toolbox Panel patched: Button syntax is now Flet 0.24+ compliant.")
    else:
        print("⚠️ Toolbox Panel button syntax not found. It might already be fixed.")
except FileNotFoundError:
    print(f"Error: Could not find {filepath_panels}")


# --- 2. Fix the Async Clock Race Condition ---
filepath_renderer = "app/ui/canvas/renderer.py"
try:
    with open(filepath_renderer, "r", encoding="utf-8") as f:
        code_renderer = f.read()

    old_update = """    def update_all_components(self) -> None:
        try:
            self.viewport.width = self.page.window.width
            self.viewport.height = self.page.window.height
        except: pass
        self._draw_grid()"""

    # Add a guard clause to ensure the canvas is mounted before the clock draws on it
    new_update = """    def update_all_components(self) -> None:
        # Safety Check: Do not allow background clock to update before UI is mounted
        if not getattr(self, 'grid_canvas', None) or not self.grid_canvas.page:
            return
            
        try:
            self.viewport.width = self.page.window.width
            self.viewport.height = self.page.window.height
        except: pass
        self._draw_grid()"""

    if old_update in code_renderer:
        with open(filepath_renderer, "w", encoding="utf-8") as f:
            f.write(code_renderer.replace(old_update, new_update))
        print("✅ Renderer patched: Async clock race-condition resolved.")
    else:
        print("⚠️ Renderer update syntax not found. It might already be fixed.")
except FileNotFoundError:
    print(f"Error: Could not find {filepath_renderer}")