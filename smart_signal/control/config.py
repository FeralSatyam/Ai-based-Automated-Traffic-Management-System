# smart_signal/control/config.py

from dataclasses import dataclass

@dataclass
class LaneROI:
    name: str
    approach: str  # e.g., "N", "E", "S", "W"
    x1: int
    y1: int
    x2: int
    y2: int

# Example ROIs — tune coordinates for your video
LANE_ROIS = [
    LaneROI("North", "N", 100, 50, 300, 240),
    LaneROI("East",  "E",  340, 260, 600, 450),
    LaneROI("South", "S",  120, 260, 310, 450),
    LaneROI("West",  "W",  20,  120, 140, 300),
]

# Controller timing bounds
MIN_GREEN = 8      # seconds
MAX_GREEN = 30     # seconds
YELLOW_TIME = 3    # seconds
CYCLE_SOFT_LIMIT = 60  # optional soft cap