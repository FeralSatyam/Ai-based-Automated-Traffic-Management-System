from flask import Flask, render_template, Response, request, redirect, url_for
import sys, os, time, cv2, threading

# Make sure Python can see the parent folder (where smart_signal lives)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from traffic_sim_2d import run_simulation_headless

app = Flask(__name__)

current_mode = "simulation"   # simulation | camera | video
video_path = None
stop_event = threading.Event()

# --- Frame generators ---
def sim_frame_generator():
    for jpg in run_simulation_headless():
        if stop_event.is_set():
            break
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n')

def camera_frame_generator(cam_index=0):
    cap = cv2.VideoCapture(cam_index)
    while cap.isOpened() and not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            break
        ok, buf = cv2.imencode(".jpg", frame)
        if not ok: continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')
    cap.release()

def video_frame_generator(path):
    cap = cv2.VideoCapture(path)
    while cap.isOpened() and not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            break
        ok, buf = cv2.imencode(".jpg", frame)
        if not ok: continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')
        time.sleep(1/30)  # pace playback
    cap.release()

# --- Routes ---
@app.route("/")
def index():
    return render_template("dashboard.html", mode=current_mode, video_path=video_path)

@app.route("/video_feed")
def video_feed():
    stop_event.clear()
    if current_mode == "simulation":
        gen = sim_frame_generator()
    elif current_mode == "camera":
        gen = camera_frame_generator(0)
    elif current_mode == "video" and video_path:
        gen = video_frame_generator(video_path)
    else:
        def empty():
            while not stop_event.is_set():
                time.sleep(0.1)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n\r\n')
        gen = empty()
    return Response(gen, mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/set_mode", methods=["POST"])
def set_mode():
    global current_mode, video_path
    mode = request.form.get("mode")
    stop_event.set()
    time.sleep(0.2)
    if mode == "video":
        f = request.files.get("video_file")
        if f and f.filename:
            save_to = os.path.join("uploads", f.filename)
            os.makedirs("uploads", exist_ok=True)
            f.save(save_to)
            video_path = save_to
            current_mode = "video"
    elif mode in ("simulation", "camera"):
        current_mode = mode
    else:
        current_mode = "stop"
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, threaded=True)