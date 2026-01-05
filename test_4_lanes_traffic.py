import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
from smart_signal.perception.detector import YOLODetector
from smart_signal.perception.tracker import IOUTracker

# -------------------------------
# Priority-based cycle controller
# -------------------------------
class PriorityCycleController:
    def __init__(self, approaches=["N","E","S","W"], min_green=5, max_green=20, yellow=3):
        self.approaches = approaches
        self.min_green = min_green
        self.max_green = max_green
        self.yellow = yellow
        self.priority_list = []
        self.current_idx = 0

    def start_cycle(self, counts):
        self.priority_list = sorted(
            self.approaches,
            key=lambda a: counts.get(a, 0),
            reverse=True
        )
        self.current_idx = 0

    def next_phase(self, counts):
        if not self.priority_list:
            self.start_cycle(counts)

        approach = self.priority_list[self.current_idx]
        count = counts.get(approach, 0)
        green = max(self.min_green, min(self.max_green, count * 2))
        yellow = self.yellow

        self.current_idx += 1
        if self.current_idx >= len(self.priority_list):
            self.priority_list = []

        return approach, green, yellow

# -------------------------------
# Paths to your 4 lane images (PNG)
# -------------------------------
IMAGE_PATHS = {
    "N": "test_images/north.png",
    "E": "test_images/east.png",
    "S": "test_images/south.png",
    "W": "test_images/west.png",
}

# -------------------------------
# UI
# -------------------------------
class TrafficUI(ctk.CTk):
    def __init__(self, controller, detector, tracker, frames):
        super().__init__()
        self.title("🚦 Smart Traffic Light Simulator")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}+0+0")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Layout
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left panel
        control_frame = ctk.CTkFrame(self, width=300)
        control_frame.grid(row=0, column=0, sticky="ns", padx=10, pady=10)
        control_frame.grid_propagate(False)

        self.status_label = ctk.CTkLabel(control_frame, text="Simulation Ready",
                                         font=ctk.CTkFont(size=14))
        self.status_label.pack(pady=10)

        self.phase_label = ctk.CTkLabel(control_frame, text="Phase: -",
                                        font=ctk.CTkFont(size=16, weight="bold"))
        self.phase_label.pack(pady=(15, 5))

        self.time_label = ctk.CTkLabel(control_frame, text="Time left: - s",
                                       font=ctk.CTkFont(size=14))
        self.time_label.pack(pady=(0, 10))

        # Counts table
        self.counts_frame = ctk.CTkFrame(control_frame)
        self.counts_frame.pack(pady=10, fill="x")
        ctk.CTkLabel(self.counts_frame, text="Vehicle Counts",
                     font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=(8,4))
        self.count_labels = {}
        for i, a in enumerate(["N", "E", "S", "W"], start=1):
            ctk.CTkLabel(self.counts_frame, text=f"{a}:", font=ctk.CTkFont(size=13)).grid(row=i, column=0, sticky="w", padx=10, pady=4)
            lab = ctk.CTkLabel(self.counts_frame, text="0", font=ctk.CTkFont(size=13))
            lab.grid(row=i, column=1, sticky="e", padx=10, pady=4)
            self.count_labels[a] = lab

        # Controls
        btn_frame = ctk.CTkFrame(control_frame)
        btn_frame.pack(pady=15, fill="x")
        self.start_btn = ctk.CTkButton(btn_frame, text="▶ Start", command=self.start_sim)
        self.start_btn.pack(pady=10, padx=10, fill="x")
        self.quit_btn = ctk.CTkButton(btn_frame, text="⏹ Quit", hover_color="#aa0000", command=self.quit)
        self.quit_btn.pack(pady=10, padx=10, fill="x")

        # Right panel
        self.video_frame = ctk.CTkFrame(self)
        self.video_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.video_frame.grid_columnconfigure(0, weight=1)
        self.video_frame.grid_rowconfigure(0, weight=1)
        self.video_label = ctk.CTkLabel(self.video_frame, text="")
        self.video_label.grid(row=0, column=0, sticky="nsew")

        # Simulation state
        self.running = False
        self.controller = controller
        self.detector = detector
        self.tracker = tracker
        self.frames = frames
        self.fid = 0
        self.current_approach = None
        self.green_left = 0
        self.yellow_left = 0
        self._last_imgtk = None

    def start_sim(self):
        self.running = True
        self.status_label.configure(text="Simulation Running")
        self.loop()

    def stop_sim(self):
        self.running = False
        self.status_label.configure(text="Simulation Paused")

    def loop(self):
        if not self.running:
            return

        counts, processed_frames = {}, {}
        for approach, frame in self.frames.items():
            if frame is None:
                continue
            detections = self.detector.infer(frame, self.fid, approach)
            tracks = self.tracker.update(detections, self.fid)
            counts[approach] = len(tracks)

            fcopy = frame.copy()
            for tr in tracks:
                x1, y1, x2, y2 = map(int, tr.bbox)
                cv2.rectangle(fcopy, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(fcopy, f"ID {tr.track_id} {tr.cls}", (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            processed_frames[approach] = fcopy

        # Phase control
        if self.green_left > 0:
            self.green_left -= 1
        elif self.yellow_left > 0:
            self.yellow_left -= 1
            if self.yellow_left == 0:
                self.current_approach, g, y = self.controller.next_phase(counts)
                self.green_left, self.yellow_left = g, 0
        else:
            self.current_approach, g, y = self.controller.next_phase(counts)
            self.green_left, self.yellow_left = g, 0

        # Update side panel
        phase_text = f"Phase: {self.current_approach or '-'}"
        if self.green_left > 0:
            time_text = f"Time left: {self.green_left} s (GREEN)"
        elif self.yellow_left > 0:
            time_text = f"Time left: {self.yellow_left} s (YELLOW)"
        else:
            time_text = "Time left: - s"
        self.phase_label.configure(text=phase_text)
        self.time_label.configure(text=time_text)
        for a in ["N", "E", "S", "W"]:
            self.count_labels[a].configure(text=str(counts.get(a, 0)))

        # Overlay signal state
        for approach, frame in processed_frames.items():
            if approach == self.current_approach and self.green_left > 0:
                color, status = (0, 255, 0), f"GREEN {self.green_left}s"
            elif approach == self.current_approach and self.yellow_left > 0:
                color, status = (0, 255, 255), f"YELLOW {self.yellow_left}s"
            else:
                color, status = (0, 0, 255), "RED"
            cv2.putText(frame, f"{approach}: {status} | Cars: {counts.get(approach,0)}",
                        (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
        # Display combined grid
        tile_w, tile_h = 400, 300

        def fit_aspect(img, tw, th):
            if img is None:
                return None
            h, w = img.shape[:2]
            scale = min(tw / w, th / h)
            new_w, new_h = int(w * scale), int(h * scale)
            return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        def pad_to_tile(img, tw, th):
            if img is None:
                return None
            h, w = img.shape[:2]
            top = (th - h) // 2
            bottom = th - h - top
            left = (tw - w) // 2
            right = tw - w - left
            return cv2.copyMakeBorder(img, top, bottom, left, right,
                                      cv2.BORDER_CONSTANT, value=(0,0,0))

        # Fit and pad each lane
        n = pad_to_tile(fit_aspect(processed_frames.get("N"), tile_w, tile_h), tile_w, tile_h)
        e = pad_to_tile(fit_aspect(processed_frames.get("E"), tile_w, tile_h), tile_w, tile_h)
        s = pad_to_tile(fit_aspect(processed_frames.get("S"), tile_w, tile_h), tile_w, tile_h)
        w_ = pad_to_tile(fit_aspect(processed_frames.get("W"), tile_w, tile_h), tile_w, tile_h)

        # Concatenate into 2×2 grid
        top = cv2.hconcat([n, e]) if n is not None and e is not None else None
        bottom = cv2.hconcat([s, w_]) if s is not None and w_ is not None else None
        if top is not None and bottom is not None:
            grid = cv2.vconcat([top, bottom])
            img_rgb = cv2.cvtColor(grid, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            imgtk = ImageTk.PhotoImage(image=pil_img)
            self.video_label.configure(image=imgtk)
            self.video_label.image = imgtk
            self._last_imgtk = imgtk

        self.fid += 1
        # Schedule next loop iteration (~2 FPS for clarity)
        self.after(500, self.loop)
if __name__ == "__main__":
    detector = YOLODetector("yolov8n.pt", conf_thresh=0.35)
    tracker = IOUTracker(iou_thresh=0.3, max_age=10)
    controller = PriorityCycleController(["N", "E", "S", "W"])

    frames = {k: cv2.imread(v) for k, v in IMAGE_PATHS.items()}
    app = TrafficUI(controller, detector, tracker, frames)
    app.mainloop()
