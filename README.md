# ⚡ PyLogic Simulator

An advanced, browser-based Digital Logic EDA Platform built entirely in Python using Flet and WebAssembly.

PyLogic Simulator is a full-featured Logisim-inspired digital logic simulator that combines:
- Real-time combinational and sequential simulation
- Infinite-canvas circuit editing
- Orthogonal wiring and routing
- Drag-and-drop interactive design
- Bus and hierarchical subcircuit support
- Browser deployment using WebAssembly
- Modular software engineering architecture

---

# ✨ Features

## 🧠 Core Simulation Engine
- Event-driven propagation engine
- Breadth-first deterministic evaluation queues
- Observer-pattern wire architecture
- Dirty-node incremental recomputation
- Multi-bit vectorized signal propagation
- Loop detection and propagation safety
- Real-time combinational logic simulation

## ⏱ Sequential Logic & Timing
- Global clock orchestration system
- Rising-edge and falling-edge triggering
- D Flip-Flops
- JK Flip-Flops
- T Flip-Flops
- SR Latches
- Step-by-step simulation execution
- Adjustable clock frequencies

## 🎨 Interactive Editor
- Infinite zoomable/pannable canvas
- Drag-and-drop component placement
- Grid snapping
- Multi-layer rendering architecture
- Dynamic property inspector
- Component toolbox system
- Selection and movement systems
- Live wire rerouting

## 🔌 Routing & Wiring
- Orthogonal Manhattan routing
- Dynamic rerouting heuristics
- Junction detection
- Wire validation
- Signal-state coloring
- Live propagation visualization
- Bus-aware routing support

## 📦 Advanced Features
- Multi-bit buses
- Splitters and mergers
- Hierarchical subcircuits
- Custom ICs
- Undo/Redo command system
- Copy/Paste
- SVG export
- PNG export
- Deterministic serialization

## 🚀 Performance Engineering
- Dirty-region rendering
- Viewport culling
- Event batching
- Incremental propagation
- Memory-safe cleanup
- WebAssembly/browser optimization
- Large-circuit scalability

## 🧪 Testing & Reliability
- Unit testing
- Integration testing
- Stress testing
- Serialization validation
- Timing validation
- Routing validation
- Large-circuit benchmarking

---

# 🏗 Architecture

PyLogic uses a strictly decoupled Event-Driven MVC architecture.

```text
┌─────────────────────────────┐
│        Frontend UI          │
│     (Flet Canvas Layer)     │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│        UI Bridge Layer      │
│      (Controller Bridge)    │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│      Simulation Engine      │
│   (Pure Python Backend)     │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│      Serialization Layer    │
│    JSON + Schema System     │
└─────────────────────────────┘
```

---

# 📂 Project Structure

```text
app/
├── main.py
├── engine/
│   ├── simulation/
│   ├── components/
│   ├── timing/
│   ├── buses/
│   ├── routing/
│   ├── serialization/
│   ├── events/
│   ├── diagnostics/
│   ├── history/
│   └── testing/
├── ui/
│   ├── bridge/
│   ├── canvas/
│   ├── toolbox/
│   ├── inspector/
│   ├── themes/
│   └── controls/
└── exports/
```

---

# ⚙️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core language |
| Flet | UI Framework |
| WebAssembly | Browser execution |
| Pytest | Testing framework |
| JSON | Serialization |
| Event Bus | Reactive architecture |

---

# 📖 Phase-by-Phase Development

## Phase 1 — Core Simulation Engine
Implemented:
- Observer-pattern wires
- Primitive gates
- Base component abstractions
- Signal propagation
- Loop detection
- Deterministic evaluation

## Phase 2 — Infinite Canvas UI
Implemented:
- Infinite canvas
- Zoom and pan
- Coordinate transforms
- Grid rendering
- UI wrappers

## Phase 3 — Routing & Wiring
Implemented:
- Orthogonal routing
- Junction systems
- Wire rendering
- Connection validation
- Live signal coloring

## Phase 4 — Real-Time Simulation
Implemented:
- Event-driven propagation
- Incremental updates
- Simulation orchestrator
- Reactive UI synchronization

## Phase 5 — Sequential Logic
Implemented:
- Global clocks
- Edge detection
- Sequential components
- Timing systems
- Step execution

## Phase 6 — Serialization
Implemented:
- Save/load systems
- JSON schemas
- Validation systems
- Restoration pipelines

## Phase 7 — Testing & QA
Implemented:
- Unit testing
- Integration testing
- Stress testing
- Reliability infrastructure
- Debugging tools

## Phase 7.5 — Interactive Editing
Implemented:
- Drag/drop placement
- Toolbox system
- Component factories
- Property inspector
- Selection systems

## Phase 8 — Optimization
Implemented:
- Rendering optimization
- Event optimization
- Memory cleanup
- Large-circuit scalability
- Browser performance tuning

## Phase 9 — Deployment
Implemented:
- WebAssembly deployment
- Browser packaging
- Static hosting workflows
- Production configuration

## Phase 10 — Advanced Features
Implemented:
- Buses
- Splitters
- Hierarchical subcircuits
- Custom ICs
- Export systems
- Undo/Redo systems

---

# 🧮 Component Library

## Basic Gates
- AND
- OR
- NOT
- NAND
- NOR
- XOR
- XNOR

## I/O Components
- Toggle Switch
- Push Button
- LED
- 7 Segment Display
- Clock Generator

## Sequential Components
- SR Latch
- D Flip-Flop
- JK Flip-Flop
- T Flip-Flop

## Advanced Components
- Bus Splitters
- Bus Mergers
- Custom ICs
- Subcircuits

---

# 💾 Serialization

PyLogic uses deterministic JSON serialization.

Example:

```json
{
  "version": "1.0",
  "components": [],
  "wires": [],
  "ui": {},
  "metadata": {}
}
```

Features:
- UUID-based identification
- Version-safe schemas
- Graph reconstruction
- Safe deserialization
- Browser-compatible persistence

---

# ⌨️ Controls & Shortcuts

| Action | Shortcut |
|---|---|
| Pan Canvas | Left Click + Drag |
| Zoom | Scroll Wheel |
| Draw Wire | Drag Pin → Pin |
| Delete Component | Right Click |
| Copy | Ctrl/Cmd + C |
| Paste | Ctrl/Cmd + V |
| Undo | Ctrl/Cmd + Z |
| Redo | Ctrl/Cmd + Shift + Z |
| Cancel Tool | ESC |

---

# 🚀 Getting Started

## Prerequisites

- Python 3.11+
- Flet

## Installation

```bash
git clone https://github.com/yourusername/pylogic-simulator.git
cd pylogic-simulator
pip install flet
```

## Run Locally

```bash
python main.py
```

## Run in Browser

```bash
flet run --web main.py
```

---

# 🌐 Deployment

Supported hosting platforms:
- GitHub Pages
- Vercel
- Static hosting providers

The application is fully browser-runnable using WebAssembly and requires no backend server.

---

# 🧪 Testing

Run all tests:

```bash
pytest
```

Testing includes:
- Logic validation
- Timing validation
- Routing tests
- Serialization tests
- Stress tests
- Integration tests

---

# 🔮 Future Roadmap

Planned future features:
- HDL export (Verilog/VHDL)
- Oscilloscope waveform viewer
- FPGA toolchain integration
- Collaborative editing
- Plugin ecosystem
- AI-assisted circuit generation
- Desktop packaging
- Mobile support

---

# 📜 License

This project is licensed under the Personal License.

---

# 🙌 Acknowledgements

Inspired by:
- Logisim
- Digital logic education tools
- Modern browser-based engineering platforms

Built with a focus on:
- software engineering quality
- educational value
- extensibility
- browser accessibility
