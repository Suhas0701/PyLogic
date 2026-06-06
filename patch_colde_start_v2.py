import os

filepath_bridge = "app/ui/bridge.py"

with open(filepath_bridge, "r", encoding="utf-8") as f:
    code_bridge = f.read()

# The regressed Phase 6 code
old_bridge = """            Wire(backend_source, backend_target)
            self.engine.detect_loops()
            
            ui_wire = UIWire(out_uipin, in_uipin, backend_source)
            self.renderer.ui_wires.append(ui_wire)
            self.engine.run_until_stable()"""

# The correct code with the Cold Start fix restored
new_bridge = """            Wire(backend_source, backend_target)
            self.engine.detect_loops()
            
            ui_wire = UIWire(out_uipin, in_uipin, backend_source)
            self.renderer.ui_wires.append(ui_wire)
            
            # RESTORED: Force initial state propagation on connection to prevent Deadlock
            try:
                backend_target.set_state(backend_source.state)
            except AttributeError:
                pass
            self.engine.queue_evaluation(in_uipin.gate.backend_comp)
            
            self.engine.run_until_stable()"""

if old_bridge in code_bridge:
    with open(filepath_bridge, "w", encoding="utf-8") as f:
        f.write(code_bridge.replace(old_bridge, new_bridge))
    print("✅ Cold-Start Deadlock fix restored to Phase 6 architecture!")
else:
    print("⚠️ Could not find the target code block. It might already be patched.")