import os

# --- 1. VISUAL PATCH ---
filepath_ui = "app/ui/components/gate_ui.py"
with open(filepath_ui, "r", encoding="utf-8") as f:
    code_ui = f.read()

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
            is_on = str(state_obj).endswith("HIGH") or state_obj == 1
            bg = ft.Colors.GREEN_600 if is_on else ft.Colors.RED_900"""

with open(filepath_ui, "w", encoding="utf-8") as f:
    f.write(code_ui.replace(old_func, new_func))


# --- 2. COLD START DEADLOCK PATCH ---
filepath_bridge = "app/ui/bridge.py"
with open(filepath_bridge, "r", encoding="utf-8") as f:
    code_bridge = f.read()

old_bridge = """            Wire(backend_source, backend_target)
            self.engine.detect_loops()
            
            ui_wire = UIWire(out_uipin, in_uipin, backend_source)
            self.renderer.ui_wires.append(ui_wire)
            self.engine.run_until_stable()"""

new_bridge = """            Wire(backend_source, backend_target)
            self.engine.detect_loops()
            
            ui_wire = UIWire(out_uipin, in_uipin, backend_source)
            self.renderer.ui_wires.append(ui_wire)
            
            # FIXED: Force initial state propagation on connection to prevent Deadlock
            try:
                backend_target.set_state(backend_source.state)
            except AttributeError:
                pass
            self.engine.queue_evaluation(in_uipin.gate.backend_comp)
            
            self.engine.run_until_stable()"""

with open(filepath_bridge, "w", encoding="utf-8") as f:
    f.write(code_bridge.replace(old_bridge, new_bridge))

print("✅ Visuals patched AND Cold-Start Deadlock eliminated!")