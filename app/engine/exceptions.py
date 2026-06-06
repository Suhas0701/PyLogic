class SimulationError(Exception):
    pass

class CircuitLoopError(SimulationError):
    pass

class InvalidConnectionError(SimulationError):
    pass
