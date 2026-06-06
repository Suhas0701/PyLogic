import os

filepath = "app/ui/canvas/renderer.py"

try:
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    patched = False
    with open(filepath, "w", encoding="utf-8") as f:
        for line in lines:
            if "self.page.launch_url(data_uri" in line:
                # The ultimate version-proof call. 
                f.write('        self.page.launch_url(data_uri)\n')
                patched = True
            else:
                f.write(line)
                
    if patched:
        print("✅ Success! Flet 'launch_url' stripped of version-breaking kwargs. Save is now bulletproof.")
    else:
        print("⚠️ Could not find the line to patch.")

except FileNotFoundError:
    print(f"Error: Could not find {filepath}. Make sure you are in the root directory.")