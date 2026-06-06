import time
from typing import Dict

class EngineProfiler:
    """Tracks performance metrics for the simulation engine and UI rendering."""
    def __init__(self):
        self.metrics: Dict[str, float] = {
            "last_engine_tick_ms": 0.0,
            "last_render_ms": 0.0,
            "total_components": 0,
            "culled_objects": 0
        }
        self._timers = {}

    def start(self, name: str):
        self._timers[name] = time.perf_counter()

    def stop(self, name: str):
        if name in self._timers:
            elapsed_ms = (time.perf_counter() - self._timers[name]) * 1000
            self.metrics[name] = elapsed_ms
            
    def get_summary(self) -> str:
        return (f"Engine: {self.metrics['last_engine_tick_ms']:.1f}ms | "
                f"Render: {self.metrics['last_render_ms']:.1f}ms | "
                f"Culled: {self.metrics.get('culled_objects', 0)}")
