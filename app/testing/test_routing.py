import pytest
from app.ui.canvas.viewport import Point
from app.ui.canvas.routing import OrthogonalRouter

def test_forward_z_route():
    start = Point(0, 0)
    end = Point(100, 50)
    path = OrthogonalRouter.route(start, end)
    
    # Should generate 4 points for a standard Z-route
    assert len(path) == 4
    assert path[0] == start
    assert path[-1] == end
    # Middle segment should align horizontally with mid_x
    assert path[1].x == 50
    assert path[1].y == 0
    assert path[2].x == 50
    assert path[2].y == 50

def test_backward_u_route():
    start = Point(100, 0)
    end = Point(0, 50)
    path = OrthogonalRouter.route(start, end, stub=20)
    
    # Should generate 6 points for a backward U-route to avoid gate clipping
    assert len(path) == 6
    assert path[0] == start
    assert path[-1] == end
    assert path[1].x == 120 # Out stub
    assert path[4].x == -20 # In stub
