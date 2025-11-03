import customtkinter as ctk
import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SCRIPTS = {
    "Traffic Simulator (4 Lanes)": os.path.join(BASE_DIR, "demo_4_lanes.py"),
    "Vehicle Detection (Camera)": os.path.join(BASE_DIR, "test_detector.py"),
    "2D Simulation": os.path.join(BASE_DIR,"test_detector.py"),
}

def run_script(script_path):
    if not os.path.exists(script_path):
        print(f"Script {script_path} not found!")
        return
    app.withdraw()
    subprocess.call([sys.executable, script_path])
    app.deiconify()
    app.state("zoomed")   # reopen maximized

# -------------------------------
# Main App
# -------------------------------
app = ctk.CTk()
app.title("🚦 Smart Traffic System Launcher")

# Always start maximized (windowed full screen)
app.state("zoomed")

# Appearance
ctk.set_appearance_mode("dark")          # "light" or "dark"
ctk.set_default_color_theme("dark-blue") # "blue", "green", "dark-blue"

# Layout frame (centered)
frame = ctk.CTkFrame(app)
frame.pack(expand=True)

title = ctk.CTkLabel(frame, text="Smart Traffic System",
                     font=ctk.CTkFont(size=32, weight="bold"))
title.pack(pady=40)

for name, path in SCRIPTS.items():
    btn = ctk.CTkButton(frame, text=name, width=400, height=60,
                        font=ctk.CTkFont(size=18),
                        command=lambda p=path: run_script(p))
    btn.pack(pady=20)

exit_btn = ctk.CTkButton(frame, text="Exit", width=400, height=50,
                         fg_color="red", hover_color="#aa0000",
                         font=ctk.CTkFont(size=18),
                         command=app.quit)
exit_btn.pack(pady=40)

app.mainloop()