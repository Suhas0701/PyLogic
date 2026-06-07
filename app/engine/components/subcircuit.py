import json
from .base import BaseComponent
from .gates import ANDGate, ORGate, NOTGate, Splitter, Merger
from .io import ToggleSwitch, LED
from .sequential import ClockGenerator, DFlipFlop, TFlipFlop, SRLatch
from ..wire import Wire
from ..simulation.controller import SimulationController

class CustomIC(BaseComponent):
    """Encapsulates an entire circuit layout into a single, reusable component."""
    def __init__(self, component_id: str, name: str, template_json: str):
        super().__init__(component_id)
        self.name = name
        self.template_json = template_json
        
        # Give the chip its own isolated simulation universe
        self.internal_engine = SimulationController()
        
        data = json.loads(template_json)
        self.internal_inputs = []
        self.internal_outputs = []
        internal_comps = {}
        
        gate_types = {
            "AND": ANDGate, "OR": ORGate, "NOT": NOTGate, 
            "SPLITTER": Splitter, "MERGER": Merger,
            "SWITCH": ToggleSwitch, "8-BIT SWITCH": ToggleSwitch, "LED": LED,
            "CLOCK": ClockGenerator, "D_FF": DFlipFlop, "T_FF": TFlipFlop, "SR_LATCH": SRLatch
        }
        
        # 1. Spawn the internal components inside the hidden engine
        for cdata in data.get("components", []):
            g_type = cdata["type"]
            g_id = cdata["id"]
            
            if g_type == "SPLITTER": comp = Splitter(g_id, bit_width=8)
            elif g_type == "MERGER": comp = Merger(g_id, bit_width=8)
            elif g_type == "8-BIT SWITCH": comp = ToggleSwitch(g_id, bit_width=8)
            elif g_type not in gate_types: continue 
            else: comp = gate_types[g_type](g_id)
            
            self.internal_engine.add_component(comp)
            internal_comps[g_id] = comp
            
            # The Packager uses Switches as Inputs, and LEDs as Outputs
            if g_type in ["SWITCH", "8-BIT SWITCH"]:
                self.internal_inputs.append((cdata["y"], comp))
            elif g_type == "LED":
                self.internal_outputs.append((cdata["y"], comp))

        # 2. Wire the internal components together
        for wdata in data.get("wires", []):
            src = internal_comps.get(wdata["source_id"])
            tgt = internal_comps.get(wdata["target_id"])
            if src and tgt:
                try: Wire(src.outputs[wdata["source_pin"]], tgt.inputs[wdata["target_pin"]])
                except: pass
                
        # 3. Sort pins geometrically (Top to Bottom) for clean UI routing
        self.internal_inputs.sort(key=lambda x: x[0])
        self.internal_outputs.sort(key=lambda x: x[0])
        
        # 4. Expose the internal connections as External Pins on the IC
        for i, (_, comp) in enumerate(self.internal_inputs):
            w = getattr(comp.outputs["out"], 'bit_width', 1)
            self.add_input(f"in_{i}", w)
            
        for i, (_, comp) in enumerate(self.internal_outputs):
            w = getattr(comp.inputs["in"], 'bit_width', 1)
            self.add_output(f"out_{i}", w)

    def evaluate(self) -> None:
        # Step A: Pass external electricity into the internal hidden switches
        for i, (_, comp) in enumerate(self.internal_inputs):
            val = self.inputs[f"in_{i}"].state
            comp._state = val
            comp.outputs["out"].set_state(val)
            self.internal_engine.queue_evaluation(comp)
            
        # Step B: Let the hidden engine process the logic
        self.internal_engine.run_until_stable()
        
        # Step C: Pass the results from the hidden LEDs out to the external pins
        for i, (_, comp) in enumerate(self.internal_outputs):
            val = comp.inputs["in"].state
            self.outputs[f"out_{i}"].set_state(val)