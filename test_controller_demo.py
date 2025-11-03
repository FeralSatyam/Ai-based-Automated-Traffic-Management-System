# test_controller_demo.py (keep this at project root)

import cv2
from smart_signal.perception.camera import CameraStream
from smart_signal.perception.detector import YOLODetector
from smart_signal.perception.tracker import IOUTracker
from smart_signal.perception.lane_mapper import count_by_lane
from smart_signal.control.controller import AdaptiveController
from smart_signal.control.config import LANE_ROIS

def draw_overlay(frame, counts, current_approach, green_left, yellow_left):
    # Draw ROIs
    for roi in LANE_ROIS:
        color = (0, 255, 0) if roi.approach == current_approach and yellow_left == 0 else (0, 200, 255) if yellow_left > 0 and roi.approach == current_approach else (255, 255, 0)
        cv2.rectangle(frame, (roi.x1, roi.y1), (roi.x2, roi.y2), color, 2)
        cv2.putText(frame, f"{roi.name}: {counts.get(roi.approach, 0)}",
                    (roi.x1 + 5, roi.y1 + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

    # HUD
    cv2.putText(frame, f"GREEN: {current_approach}  {green_left:02d}s | YELLOW: {yellow_left:02d}s",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

def main():
    cam = CameraStream(0, fps=15)  # or "assets/vehicle.mp4"
    detector = YOLODetector(model_path="yolov8n.pt", conf_thresh=0.35)
    tracker = IOUTracker(iou_thresh=0.3, max_age=10)
    controller = AdaptiveController(["N", "E", "S", "W"])

    # Initial state
    current_approach, green_time, yellow_time = "N", 8, 0
    green_left, yellow_left = green_time, 0

    for fid, ts, frame in cam.frames():
        # Perception
        detections = detector.infer(frame, fid, current_approach)  # cls filtering optional
        tracks = tracker.update(detections, fid)

        # Counting
        counts = count_by_lane(tracks)

        # Phase timing
        if green_left > 0:
            green_left -= 1
            controller.tick(1)
        elif yellow_left > 0:
            yellow_left -= 1
            controller.tick(1)
        else:
            # Decide next cycle based on current counts
            next_approach, next_green, next_yellow = controller.decide(counts)
            current_approach, green_time, yellow_time = next_approach, next_green, next_yellow
            green_left, yellow_left = green_time, 0

        # Transition to yellow when green finishes
        if green_left == 0 and yellow_left == 0:
            yellow_left = yellow_time

        # Visualization
        for tr in tracks:
            x1, y1, x2, y2 = map(int, tr.bbox)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID {tr.track_id} {tr.cls}", (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        draw_overlay(frame, counts, current_approach, green_left, yellow_left)

        cv2.imshow("Smart Signal Demo", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()