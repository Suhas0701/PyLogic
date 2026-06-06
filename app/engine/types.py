from enum import Enum, auto

class LogicState(Enum):
    LOW = 0
    HIGH = 1
    HIGH_Z = 2
    UNDEFINED = 3

    def __bool__(self) -> bool:
        return self == LogicState.HIGH
