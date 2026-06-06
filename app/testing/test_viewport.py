from app.ui.canvas.viewport import Viewport, Point

def test_viewport_pan():
    vp = Viewport(800, 600)
    vp.pan(100, 50)
    assert vp.camera.x == -100
    assert vp.camera.y == -50

def test_viewport_zoom():
    vp = Viewport(800, 600)
    vp.apply_zoom(2.0, 0, 0)
    assert vp.zoom == 2.0
