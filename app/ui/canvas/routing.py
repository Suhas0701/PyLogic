import math
from typing import List
from .viewport import Point

class OrthogonalRouter:
    _route_cache = {}

    @classmethod
    def route(cls, start: Point, end: Point, stub: float = 20.0) -> List[Point]:
        # PERFORMANCE: O(1) Cache lookup for static wires
        cache_key = (start.x, start.y, end.x, end.y, stub)
        if cache_key in cls._route_cache:
            return cls._route_cache[cache_key]

        path = [start]
        
        # Calculate standard orthogonal paths
        if start.x + stub < end.x - stub:
            mid_x = (start.x + end.x) / 2
            path.append(Point(mid_x, start.y))
            path.append(Point(mid_x, end.y))
        else:
            path.append(Point(start.x + stub, start.y))
            mid_y = (start.y + end.y) / 2
            path.append(Point(start.x + stub, mid_y))
            path.append(Point(end.x - stub, mid_y))
            path.append(Point(end.x - stub, end.y))
            
        path.append(end)
        
        # Bound cache size to prevent memory leaks in massive sessions
        if len(cls._route_cache) > 5000:
            cls._route_cache.clear()
            
        cls._route_cache[cache_key] = path
        return path
