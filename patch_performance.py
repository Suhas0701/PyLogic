import os

filepath = "app/ui/canvas/renderer.py"

try:
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    old_update = """    def update_all_components(self) -> None:
        # Safety Check: Do not allow background clock to update before UI is mounted
        if not getattr(self, 'grid_canvas', None) or not self.grid_canvas.page:
            return
            
        try:
            self.viewport.width = self.page.window.width
            self.viewport.height = self.page.window.height
        except: pass
        self._draw_grid() 
        self._draw_wires_and_pins()"""

    new_update = """    def update_all_components(self) -> None:
        # Safety Check: Do not allow background clock to update before UI is mounted
        if not getattr(self, 'grid_canvas', None) or not self.grid_canvas.page:
            return
            
        try:
            self.viewport.width = self.page.window.width
            self.viewport.height = self.page.window.height
        except: pass
        
        # PERFORMANCE FIX: Do not recalculate 1000+ grid dots while actively dragging a wire or gate
        is_dragging = self.wiring_start_pin is not None or self.dragging_gate is not None
        if not is_dragging:
            self._draw_grid() 
            
        self._draw_wires_and_pins()"""

    if "def update_all_components(self) -> None:" in code:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code.replace(old_update, new_update))
        print("✅ Performance patched! Grid rendering is now suspended during mouse drags.")
    else:
        print("⚠️ Could not find the update function. It might already be patched.")

except FileNotFoundError:
    print(f"Error: Could not find {filepath}.")