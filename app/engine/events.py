from typing import Callable, Dict, List

class EventDispatcher:
    """Decoupled publisher/subscriber for Engine-to-UI communication."""
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def on(self, event_name: str, callback: Callable) -> None:
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(callback)

    def emit(self, event_name: str, *args, **kwargs) -> None:
        for listener in self._listeners.get(event_name, []):
            listener(*args, **kwargs)
