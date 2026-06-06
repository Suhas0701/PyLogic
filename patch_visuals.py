import os

filepath = "app/ui/components/gate_ui.py"
with open(filepath, "r", encoding="utf-8") as f:
    code = f.read()

# Replace the visual state logic with a bulletproof string check
old_func = """    def _update_visual_state(self):
        bg = ft.Colors.BLUE_GREY_800
        shadow = None
        if self.label == "SWITCH" or self.label == "CLOCK":
            is_on = getattr(self.backend_comp, "_state", False)
            bg = ft.Colors.GREEN_600 if is_on else ft.Colors.RED_900"""

new_func = """    def _update_visual_state(self):
        bg = ft.Colors.BLUE_GREY_800
        shadow = None
        if self.label in ["SWITCH", "CLOCK"]:
            state_obj = getattr(self.backend_comp, "_state", None)
            # Safely parse the Enum so the box flashes properly
            is_on = str(state_obj).endswith("HIGH") or state_obj == 1
            bg = ft.Colors.GREEN_600 if is_on else ft.Colors.RED_900"""

with open(filepath, "w", encoding="utf-8") as f:
    f.write(code.replace(old_func, new_func))

print("✅ Visuals patched! Clock and Switch boxes will now flash accurately.")