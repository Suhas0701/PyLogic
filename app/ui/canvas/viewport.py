from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

class Viewport:
    def __init__(self, width: float = 800, height: float = 600):
        self.camera = Point(0, 0)
        self.zoom: float = 1.0
        self.grid_size: int = 20
        self.width = width
        self.height = height

    def world_to_screen(self, world_pos: Point) -> Point:
        sx = (world_pos.x - self.camera.x) * self.zoom
        sy = (world_pos.y - self.camera.y) * self.zoom
        return Point(sx, sy)

    def screen_to_world(self, screen_pos: Point) -> Point:
        wx = (screen_pos.x / self.zoom) + self.camera.x
        wy = (screen_pos.y / self.zoom) + self.camera.y
        return Point(wx, wy)

    def pan(self, dx_screen: float, dy_screen: float) -> None:
        self.camera.x -= dx_screen / self.zoom
        self.camera.y -= dy_screen / self.zoom

    def apply_zoom(self, factor: float, focal_screen_x: float, focal_screen_y: float) -> None:
        new_zoom = max(0.2, min(3.0, self.zoom * factor))
        if new_zoom == self.zoom: return
        world_focal = self.screen_to_world(Point(focal_screen_x, focal_screen_y))
        self.zoom = new_zoom
        self.camera.x = world_focal.x - (focal_screen_x / self.zoom)
        self.camera.y = world_focal.y - (focal_screen_y / self.zoom)

    def snap_to_grid(self, world_pos: Point) -> Point:
        snapped_x = round(world_pos.x / self.grid_size) * self.grid_size
        snapped_y = round(world_pos.y / self.grid_size) * self.grid_size
        return Point(snapped_x, snapped_y)
