#!/bin/bash

echo "🏗️  Scaffolding Phase 10: Advanced Architecture..."

# Create new necessary directories
mkdir -p app/core/components
mkdir -p app/exporters
mkdir -p app/ui/dialogs

# 1. Create the History Manager (Undo/Redo Command Pattern)
cat << 'EOF' > app/core/history.py
from typing import Protocol, List

class Command(Protocol):
    def execute(self) -> None: ...
    def undo(self) -> None: ...

class HistoryManager:
    def __init__(self, limit: int = 50):
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.limit = limit

    def execute(self, command: Command):
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()
        
        # Protect WebAssembly memory limits
        if len(self.undo_stack) > self.limit:
            self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack: return
        cmd = self.undo_stack.pop()
        cmd.undo()
        self.redo_stack.append(cmd)

    def redo(self):
        if not self.redo_stack: return
        cmd = self.redo_stack.pop()
        cmd.execute()
        self.undo_stack.append(cmd)
EOF

# 2. Create the Macro-Expansion Subcircuit Class
cat << 'EOF' > app/core/components/subcircuit.py
import json
from app.core.components.base import Component

class CustomIC(Component):
    """
    Encapsulates a nested circuit. Acts as a single block in the UI,
    but flattens into raw gates within the Simulation Engine.
    """
    def __init__(self, id: str, definition_json: str):
        super().__init__(id, "CUSTOM_IC")
        self.template = json.loads(definition_json)
        self.inner_components = []
        
        # Setup UI Pins based on the template's designated IO
        for ext_in in self.template.get("external_inputs", []):
            self.add_input(ext_in["name"], ext_in.get("width", 1))
            
        for ext_out in self.template.get("external_outputs", []):
            self.add_output(ext_out["name"], ext_out.get("width", 1))

    def flatten_into_engine(self, engine):
        """
        Injects internal components into the main engine namespace 
        to prevent recursive engine calls during simulation.
        """
        prefix = f"{self.id}_"
        # TODO: Implement macro-expansion graph injection
        pass

    def evaluate(self):
        # Evaluation is handled by the flattened graph in the main engine.
        pass
EOF

# 3. Create the SVG Exporter (Browser-Safe Vector Graphics)
cat << 'EOF' > app/exporters/svg_export.py
def export_to_svg(components, wires, width=1920, height=1080) -> str:
    """
    Generates a pure, scalable SVG representation of the circuit.
    100% WebAssembly safe (no local file dependencies).
    """
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">']
    svg.append('<rect width="100%" height="100%" fill="#1e1e1e"/>') # Background

    # Draw Wires
    for wire in wires:
        stroke = "#00ff00" if wire.state > 0 else "#555555"
        stroke_width = 4 if wire.bit_width > 1 else 2  # Thicker lines for buses
        
        # Assuming wire has a get_svg_path() or similar geometric representation
        path = wire.get_svg_path() if hasattr(wire, 'get_svg_path') else ""
        if path:
            svg.append(f'<path d="{path}" stroke="{stroke}" stroke-width="{stroke_width}" fill="none"/>')

    # Draw Components
    for comp in components:
        svg.append(f'<rect x="{comp.x}" y="{comp.y}" width="{comp.w}" height="{comp.h}" fill="#333" stroke="#fff"/>')
        svg.append(f'<text x="{comp.x+10}" y="{comp.y+20}" fill="#fff" font-family="monospace">{comp.type}</text>')

    svg.append('</svg>')
    return "\n".join(svg)
EOF

# 4. Initialize the exporter module
touch app/exporters/__init__.py

echo "✅ Phase 10 Scaffolding Complete!"