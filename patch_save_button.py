import os

filepath = "app/ui/canvas/renderer.py"

try:
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    # Flet deprecated 'web_window_name', we swap it to 'window_name'
    old_line = 'self.page.launch_url(data_uri, web_window_name="_blank")'
    new_line = 'self.page.launch_url(data_uri, window_name="_blank")'

    if old_line in code:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code.replace(old_line, new_line))
        print("✅ Save button patched! Flet API updated to use 'window_name'.")
    else:
        print("⚠️ Could not find the specific line. It might already be patched.")

except FileNotFoundError:
    print(f"Error: Could not find {filepath}. Make sure you are in the root directory.")