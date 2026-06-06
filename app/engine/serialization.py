import json
from typing import Dict, Any

class SchemaVersionManager:
    CURRENT_VERSION = "1.0"
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> bool:
        if "version" not in data or data["version"] != cls.CURRENT_VERSION:
            raise ValueError(f"Unsupported schema version: {data.get('version', 'Unknown')}")
        if "components" not in data or not isinstance(data["components"], list):
            raise ValueError("Schema missing 'components' array.")
        if "wires" not in data or not isinstance(data["wires"], list):
            raise ValueError("Schema missing 'wires' array.")
        return True

class CircuitSerializer:
    @staticmethod
    def export_state(bridge) -> str:
        """Extracts the unified Engine and UI state into a JSON schema."""
        state = {
            "version": SchemaVersionManager.CURRENT_VERSION,
            "metadata": {
                "clock_hz": bridge.clock_hz
            },
            "components": [],
            "wires": []
        }
        
        # Serialize Components
        for gate_id, ui_gate in bridge.renderer.ui_gates.items():
            state["components"].append({
                "id": gate_id,
                "type": ui_gate.label,
                "x": ui_gate.world_pos.x,
                "y": ui_gate.world_pos.y
            })
            
        # Serialize Wires
        for ui_wire in bridge.renderer.ui_wires:
            state["wires"].append({
                "source_id": ui_wire.source_pin.gate.gate_id,
                "source_pin": ui_wire.source_pin.pin_id,
                "target_id": ui_wire.target_pin.gate.gate_id,
                "target_pin": ui_wire.target_pin.pin_id
            })
            
        return json.dumps(state, indent=2)

class CircuitDeserializer:
    @staticmethod
    def import_state(bridge, json_string: str) -> None:
        """Safely parses JSON and reconstructs the circuit graph."""
        try:
            data = json.loads(json_string)
            SchemaVersionManager.validate(data)
        except Exception as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")

        # 1. Clear current workspace safely
        bridge.clear_workspace()

        # 2. Restore Metadata
        bridge.set_clock_hz(data.get("metadata", {}).get("clock_hz", 1.0))

        # 3. Restore Components (Forcing specific UUIDs)
        for comp in data["components"]:
            bridge.spawn_gate(
                gate_type=comp["type"], 
                world_x=comp["x"], 
                world_y=comp["y"], 
                force_id=comp["id"]
            )

        # 4. Restore Wiring Topology
        for wire in data["wires"]:
            src_gate = bridge.renderer.ui_gates.get(wire["source_id"])
            tgt_gate = bridge.renderer.ui_gates.get(wire["target_id"])
            
            if not src_gate or not tgt_gate:
                print(f"Warning: Dropping orphaned wire during load.")
                continue
                
            src_pin = next((p for p in src_gate.pins if p.pin_id == wire["source_pin"]), None)
            tgt_pin = next((p for p in tgt_gate.pins if p.pin_id == wire["target_pin"]), None)
            
            if src_pin and tgt_pin:
                bridge.attempt_connection(src_pin, tgt_pin)

        # 5. Stabilize the simulation
        bridge.engine.run_until_stable()
        bridge.renderer.update_all_components()
