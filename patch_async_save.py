import os

filepath = "app/ui/canvas/renderer.py"

try:
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    old_func = """    def _on_save(self, e):
        if not self.bridge: return
        json_str = self.bridge.export_project()
        
        # WebAssembly safe file download via Data URI
        b64_json = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        data_uri = f"data:application/json;base64,{b64_json}"
        self.page.launch_url(data_uri)
        
        # Optional fallback visual feedback
        print(json_str)"""

    new_func = """    async def _on_save(self, e):
        if not self.bridge: return
        json_str = self.bridge.export_project()
        
        # WebAssembly safe file download via Data URI
        b64_json = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        data_uri = f"data:application/json;base64,{b64_json}"
        await self.page.launch_url(data_uri)
        
        print("✅ Project exported successfully!")"""

    if "def _on_save(self, e):" in code:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code.replace(old_func, new_func))
        print("✅ Save button patched! The handler is now strictly async.")
    else:
        print("⚠️ Could not find the old synchronous _on_save function.")

except FileNotFoundError:
    print(f"Error: Could not find {filepath}.")