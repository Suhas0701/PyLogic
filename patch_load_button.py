import os

filepath = "app/ui/canvas/renderer.py"

try:
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    old_load = """    def _on_load(self, e):
        self.import_textfield.value = ""
        self.page.dialog = self.import_dialog
        self.import_dialog.open = True
        self.page.update()"""

    new_load = """    def _on_load(self, e):
        print("▶️ Load button clicked! Opening dialog...")
        self.import_textfield.value = ""
        
        # Universally bulletproof dialog rendering
        if self.import_dialog not in self.page.overlay:
            self.page.overlay.append(self.import_dialog)
            
        self.import_dialog.open = True
        self.page.update()"""

    if old_load in code:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code.replace(old_load, new_load))
        print("✅ Load button patched! Using universal 'page.overlay' rendering.")
    else:
        print("⚠️ Could not find the old _on_load function. It might already be patched.")

except FileNotFoundError:
    print(f"Error: Could not find {filepath}.")