import asyncio
import uuid
from typing import Dict, Optional
from app.engine.simulation.controller import SimulationController
from app.engine.components.gates import ANDGate, ORGate, NOTGate, Splitter, Merger
from app.engine.components.io import ToggleSwitch, LED
from app.engine.components.sequential import ClockGenerator, DFlipFlop, TFlipFlop, SRLatch
from app.engine.wire import Wire
from app.engine.exceptions import InvalidConnectionError, CircuitLoopError
from app.ui.canvas.renderer import CanvasRenderer
from app.ui.components.gate_ui import UIGate
from app.ui.components.pin_ui import UIPin
from app.ui.components.wire_ui import UIWire
from app.engine.serialization import CircuitSerializer, CircuitDeserializer
from app.engine.history import HistoryManager, StateSnapshotCommand
from app.engine.profiler import EngineProfiler
from app.engine.components.subcircuit import CustomIC

class UIEngineBridge:
    def __init__(self, engine: SimulationController, renderer: CanvasRenderer):
        self.engine = engine
        self.renderer = renderer
        self.renderer.bind_bridge(self)
        
        self.profiler = EngineProfiler()
        self.is_batching = False 
        
        # Phase 10: Advanced Editing State
        self.history = HistoryManager(limit=30)
        self._pre_action_state: Optional[str] = None
        self._clipboard: Optional[Dict] = None
        # Phase 10: Custom IC Library
        self.custom_ic_library: Dict[str, str] = {}
        
        self.engine.on("state_stabilized", self._on_engine_stabilized)
        self.engine.on("error", self._on_engine_error)
        
        self.gate_types = {
            "AND": ANDGate, "OR": ORGate, "NOT": NOTGate, "SPLITTER": Splitter, "MERGER": Merger,
            "SWITCH": ToggleSwitch, "8-BIT SWITCH": ToggleSwitch, "LED": LED,
            "CLOCK": ClockGenerator, "D_FF": DFlipFlop, "T_FF": TFlipFlop, "SR_LATCH": SRLatch
        }
        
        self.clock_hz = 1.0
        self.active_tool: Optional[str] = None
        self.selected_gate: Optional[UIGate] = None
        
        self.renderer.page.run_task(self._async_clock_loop)
    
    def package_subcircuit(self, name: str):
        json_str = self.export_project()
        self.custom_ic_library[name] = json_str
        self.renderer.show_success(f"📦 IC '{name}' packaged successfully!")
        self.engine.emit("library_updated")
        self.clear_workspace() # Clear the board to let them test their new chip!

    def is_custom_ic(self, gate_type: str) -> bool:
        return gate_type in self.custom_ic_library

    def delete_custom_ic(self, name: str):
        if name in self.custom_ic_library:
            del self.custom_ic_library[name]
            if self.active_tool == name:
                self.active_tool = None
            self.renderer.show_success(f"🗑️ Deleted Custom IC: {name}")
            self.engine.emit("library_updated")
    
    def cancel_action(self):
        """Drops the current tool and clears any selection."""
        self.select_component(None)
        self.active_tool = None
        self.engine.emit("clear_active_tool")
        if not self.is_batching:
            self.renderer.update_all_components()

    async def _async_clock_loop(self):
        while True:
            await asyncio.sleep(1.0 / self.clock_hz)
            if not self.is_batching:
                self.profiler.start("last_engine_tick_ms")
                self.engine.tick_clocks()
                self.profiler.stop("last_engine_tick_ms")

    def set_clock_hz(self, hz: float):
        self.clock_hz = max(0.1, float(hz))

    def _on_engine_stabilized(self):
        if not self.is_batching:
            self.renderer.update_all_components()

    def _on_engine_error(self, message: str):
        self.renderer.show_error(message)

    def select_component(self, ui_gate: Optional[UIGate]):
        self.selected_gate = ui_gate
        self.engine.emit("selection_changed", ui_gate)

    # --- ADVANCED EDITING CAPTURES ---
    def save_state_before_action(self):
        if not self.history.is_undoing:
            self._pre_action_state = self.export_project()

    def commit_action(self):
        if not self.history.is_undoing and self._pre_action_state is not None:
            post_state = self.export_project()
            if self._pre_action_state != post_state:
                cmd = StateSnapshotCommand(self, self._pre_action_state, post_state)
                self.history.push(cmd)
            self._pre_action_state = None

    def undo(self):
        self.history.undo()

    def redo(self):
        self.history.redo()

    def copy_selection(self):
        if self.selected_gate:
            self._clipboard = {"type": self.selected_gate.label}
            self.renderer.show_success(f"Copied {self.selected_gate.label}")

    def paste_selection(self):
        if self._clipboard:
            offset = 40
            if self.selected_gate:
                sx = self.selected_gate.world_pos.x + offset
                sy = self.selected_gate.world_pos.y + offset
            else:
                sx = self.renderer.viewport.camera.x + 200
                sy = self.renderer.viewport.camera.y + 200
            
            self.spawn_gate(self._clipboard["type"], sx, sy)
    # ---------------------------------

    def spawn_gate(self, gate_type: str, world_x: float, world_y: float, force_id: Optional[str] = None) -> None:
        self.save_state_before_action()
        gate_id = force_id if force_id else str(uuid.uuid4())
        
        if self.is_custom_ic(gate_type):
            json_template = self.custom_ic_library[gate_type]
            backend_gate = CustomIC(gate_id, gate_type, json_template)
        elif gate_type.upper() == "SPLITTER": backend_gate = Splitter(gate_id, bit_width=8)
        elif gate_type.upper() == "MERGER": backend_gate = Merger(gate_id, bit_width=8)
        elif gate_type.upper() == "8-BIT SWITCH": backend_gate = ToggleSwitch(gate_id, bit_width=8)
        else: backend_gate = self.gate_types[gate_type.upper()](gate_id)
            
        self.engine.add_component(backend_gate)
        ui_gate = UIGate(gate_id, world_x, world_y, label=gate_type.upper(), backend_comp=backend_gate)
        self.renderer.add_gate(ui_gate)
        
        if not self.is_batching:
            self.select_component(ui_gate)
            self.commit_action()

    def attempt_connection(self, out_uipin: UIPin, in_uipin: UIPin) -> None:
        self.save_state_before_action()
        try:
            backend_source = out_uipin.gate.backend_comp.outputs[out_uipin.pin_id]
            backend_target = in_uipin.gate.backend_comp.inputs[in_uipin.pin_id]
            Wire(backend_source, backend_target)
            self.engine.detect_loops()
            ui_wire = UIWire(out_uipin, in_uipin, backend_source)
            self.renderer.ui_wires.append(ui_wire)
            
            try: backend_target.set_state(backend_source.state)
            except AttributeError: pass
            
            self.engine.queue_evaluation(in_uipin.gate.backend_comp)
            
            if not self.is_batching:
                self.engine.run_until_stable()
                self.renderer.update_all_components()
                self.commit_action()
                
        except (InvalidConnectionError, CircuitLoopError) as e:
            self.renderer.show_error(str(e))
            self._pre_action_state = None # Abort history save
            if isinstance(e, CircuitLoopError): backend_target.connected_wire.disconnect()

    def remove_connection(self, in_uipin: UIPin) -> None:
        self.save_state_before_action()
        wire_to_remove = next((w for w in self.renderer.ui_wires if w.target_pin == in_uipin), None)
        if wire_to_remove:
            self.renderer.ui_wires.remove(wire_to_remove)
            backend_target = in_uipin.gate.backend_comp.inputs[in_uipin.pin_id]
            backend_wire = backend_target.connected_wire

            if backend_wire:
                if backend_wire in backend_wire.source.connected_wires:
                    backend_wire.source.connected_wires.remove(backend_wire)
                backend_target.connected_wire = None
                backend_target.state = 0

            self.engine.queue_evaluation(in_uipin.gate.backend_comp)
            if not self.is_batching:
                self.engine.run_until_stable()
                self.renderer.update_all_components()
                self.commit_action()

    def delete_selected(self) -> None:
        if not self.selected_gate: return
        self.save_state_before_action()
        gate = self.selected_gate

        for pin in gate.pins:
            if pin.is_input: self.remove_connection(pin)
            else:
                wires_to_remove = [w for w in self.renderer.ui_wires if w.source_pin == pin]
                for w in wires_to_remove: self.remove_connection(w.target_pin)

        del self.renderer.ui_gates[gate.gate_id]
        self.renderer.gates_layer.controls.remove(gate.control)

        if gate.backend_comp in self.engine.components:
            self.engine.components.remove(gate.backend_comp)
        if gate.backend_comp in self.engine.clocks:
            self.engine.clocks.remove(gate.backend_comp)

        self.select_component(None)
        if not self.is_batching:
            self.engine.run_until_stable()
            self.renderer.update_all_components()
            self.commit_action()

    def handle_interaction(self, ui_gate: UIGate) -> None:
        if isinstance(ui_gate.backend_comp, ToggleSwitch):
            ui_gate.backend_comp.toggle()
            self.engine.run_until_stable()
            self.renderer.update_all_components()

    def clear_workspace(self) -> None:
        self.save_state_before_action()
        self.select_component(None)
        self.engine.components.clear()
        self.engine.clocks.clear()
        self.engine._eval_queue.clear()
        self.engine._in_queue.clear()
        self.renderer.ui_gates.clear()
        self.renderer.ui_wires.clear()
        self.renderer.gates_layer.controls.clear()
        self.renderer.wire_canvas.shapes.clear()
        self.renderer.update_all_components()
        self.commit_action()

    def export_project(self) -> str:
        return CircuitSerializer.export_state(self)

    def import_project(self, json_string: str) -> None:
        self.import_project_silent(json_string)

    def import_project_silent(self, json_string: str) -> None:
        try:
            self.is_batching = True
            CircuitDeserializer.import_state(self, json_string)
        except ValueError as e:
            if not self.history.is_undoing: self.renderer.show_error(str(e))
        finally:
            self.is_batching = False
            self.engine.run_until_stable()
            self.renderer.update_all_components()