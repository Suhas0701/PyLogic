from ..canvas.viewport import Point

class UIPin:
    def __init__(self, gate, pin_id: str, is_input: bool, rel_x: float, rel_y: float):
        self.gate = gate
        self.pin_id = pin_id
        self.is_input = is_input
        self.rel_x = rel_x
        self.rel_y = rel_y
        self.radius = 6.0

    @property
    def global_pos(self) -> Point:
        return Point(
            self.gate.world_pos.x + self.rel_x,
            self.gate.world_pos.y + self.rel_y
        )
