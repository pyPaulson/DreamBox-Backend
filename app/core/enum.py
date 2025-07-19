from enum import Enum

class PlanType(str, Enum):
    SAFELOCK = "safelock"
    MYGOAL = "mygoal"
    FLEXI = "flexi"
    EMERGENCY = "emergency"
