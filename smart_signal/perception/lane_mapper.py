# smart_signal/perception/lane_mapper.py

from typing import List, Dict, Tuple
from smart_signal.control.config import LANE_ROIS
import numpy as np

def bbox_centroid(bbox: Tuple[float, float, float, float]) -> Tuple[int, int]:
    x1, y1, x2, y2 = bbox
    cx = int((x1 + x2) / 2)
    cy = int((y1 + y2) / 2)
    return cx, cy

def point_in_rect(px: int, py: int, x1: int, y1: int, x2: int, y2: int) -> bool:
    return (x1 <= px <= x2) and (y1 <= py <= y2)

def count_by_lane(tracks: List) -> Dict[str, int]:
    # tracks: objects with .bbox and .track_id
    counts = {roi.approach: 0 for roi in LANE_ROIS}
    for tr in tracks:
        cx, cy = bbox_centroid(tr.bbox)
        for roi in LANE_ROIS:
            if point_in_rect(cx, cy, roi.x1, roi.y1, roi.x2, roi.y2):
                counts[roi.approach] += 1
                break
    return counts