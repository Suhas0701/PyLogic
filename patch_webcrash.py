import os

filepath = "app/ui/canvas/renderer.py"

try:
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    old_update = """        try:
            self.viewport.width = self.page.window.width
            self.viewport.height = self.page.window.height
        except: pass"""

    new_update = """        try:
            # Web-safe dimension retrieval
            vw = getattr(self.page, "width", None)
            vh = getattr(self.page, "height", None)
            if not vw and hasattr(self.page, "window"): vw = self.page.window.width
            if not vh and hasattr(self.page, "window"): vh = self.page.window.height
            
            # Ensure they are never None
            self.viewport.width = vw or 800
            self.viewport.height = vh or 600
        except: pass"""

    if old_update in code:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code.replace(old_update, new_update))
        print("✅ Renderer Patched: WebAssembly window dimension crash fixed!")
    else:
        print("⚠️ Could not find the exact code to patch. It might already be fixed.")

except FileNotFoundError:
    print(f"Error: Could not find {filepath}.")