from typing import Protocol, List

class Command(Protocol):
    def execute(self) -> None: ...
    def undo(self) -> None: ...

class StateSnapshotCommand:
    """Captures the entire circuit state as JSON for flawless Undo/Redo."""
    def __init__(self, bridge, before_json: str, after_json: str):
        self.bridge = bridge
        self.before_json = before_json
        self.after_json = after_json

    def execute(self):
        self.bridge.import_project_silent(self.after_json)

    def undo(self):
        self.bridge.import_project_silent(self.before_json)

class HistoryManager:
    def __init__(self, limit: int = 50):
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.limit = limit
        self.is_undoing = False # Prevents recursion loops during deserialization

    def push(self, command: Command):
        if self.is_undoing: return
        self.undo_stack.append(command)
        self.redo_stack.clear()
        
        # Protect WebAssembly memory limits
        if len(self.undo_stack) > self.limit:
            self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack: return
        self.is_undoing = True
        cmd = self.undo_stack.pop()
        cmd.undo()
        self.redo_stack.append(cmd)
        self.is_undoing = False

    def redo(self):
        if not self.redo_stack: return
        self.is_undoing = True
        cmd = self.redo_stack.pop()
        cmd.execute()
        self.undo_stack.append(cmd)
        self.is_undoing = False