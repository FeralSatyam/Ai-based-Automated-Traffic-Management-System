# smart_signal/simulation/sim_detector.py
import numpy as np
from typing import List
from smart_signal.types import Detection
from smart_signal.simulation.sim_core import SimWorld

class SimulationDetector:
    """
    Adapts the SimWorld vehicles to Detection objects (no ML).
    """
    def __init__(self, world: SimWorld):
        self.world = world

    def infer(self, frame, frame_id: int, approach_id: str) -> List[Detection]:
        dets: List[Detection] = []
        for v in self.world.vehicles:
            # Simple bbox from vehicle rect
            x1, y1 = v.x, v.y
            x2, y2 = v.x + (36 if v.direction in ("E","W") else 20), v.y + (36 if v.direction in ("N","S") else 20)
            dets.append(Detection(
                bbox=(float(x1), float(y1), float(x2), float(y2)),
                score=0.99,
                cls="car",
                frame_id=frame_id,
                approach_id=v.approach_id  # approach by origin
            ))
        return dets

def surface_to_frame(surface) -> np.ndarray:
    """
    Convert Pygame surface to BGR numpy array for OpenCV display if needed.
    """
    arr = np.transpose(np.array(pygame.surfarray.pixels3d(surface)), (1,0,2))
    return arr[:, :, ::-1].copy()