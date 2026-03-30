# Smart Traffic Management System

An intelligent traffic management solution that optimizes traffic flow at intersections using computer vision and AI technologies. This project was developed by Team Quantum Coders for the Codarambha Hackathon.

## 🚦 Overview

The system uses real-time video processing to detect vehicles, track their movement, and intelligently control traffic signals to minimize congestion and waiting times at intersections.

## ✨ Key Features

- Real-time vehicle detection using YOLOv8
- Multi-lane traffic monitoring
- Intelligent traffic signal timing optimization
- Traffic simulation for testing scenarios

## 🛠️ Technologies Used

- Python
- YOLOv8 for object detection
- OpenCV for image processing
- Flask for web interface
- JavaScript for frontend visualization

## 📦 Installation

1. **Clone the repository**
```bash
git clone https://github.com/FeralSatyam/Ai-based-Automated-Traffic-Management-System
cd Ai-based-Automated-Traffic-Management-System Public
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Install the package**
```bash
pip install -e .
```

## 🚀 Quick Start

1. **Run the Project**
```bash
python launcher.py
```

2. **Launch the web interface**
```bash
python app.py
```
Then visit `http://localhost:5000` in your browser

## 📁 Project Structure

```
├── app.py                    # Web application entry point
├── demo_4_lanes.py          # Demo simulation script
├── smart_signal/            # Core package
│   ├── perception/         # Computer vision components
│   ├── control/           # Traffic control logic
│   ├── simulation/        # Traffic simulation
│   └── utils/            # Utility functions
├── config/                # Configuration files
├── static/               # Web assets
└── templates/            # HTML templates
```

## ⚙️ Configuration

The system can be configured through `config/config.yaml`. Key settings include:

- Detection parameters
- Traffic signal timing
- Lane configurations
- Simulation settings




## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- YOLOv8 team for the object detection model
- OpenCV community
