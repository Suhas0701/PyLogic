import os

filepath = "app/ui/canvas/renderer.py"

try:
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    old_methods = """    def _on_step(self, e):
        if self.bridge:
            self.bridge.engine.step()
            self.update_all_components()"""

    new_methods = """    def _on_step(self, e):
        if self.bridge:
            self.bridge.engine.step()
            self.update_all_components()

    def _on_hz_change(self, e):
        self.hz_text.value = f"{int(e.control.value)} Hz"
        if self.bridge: self.bridge.set_clock_hz(e.control.value)
        self.toolbar.update()"""

    if old_methods in code and "def _on_hz_change" not in code:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code.replace(old_methods, new_methods))
        print("✅ Missing '_on_hz_change' method seamlessly restored to the Renderer!")
    elif "def _on_hz_change" in code:
        print("⚠️ The method is already in the file.")
    else:
        print("⚠️ Could not find the exact insertion point. You may need to paste it manually.")

except FileNotFoundError:
    print(f"Error: Could not find {filepath}.")