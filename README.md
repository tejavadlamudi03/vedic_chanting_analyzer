# 🕉 Vedic Chanting Analyzer — ROS2 Project

> ⚠️ **This project is currently under active development.** Features may be incomplete or subject to change.

![Status](https://img.shields.io/badge/status-under%20development-orange)
![ROS2](https://img.shields.io/badge/ROS2-Humble-blue)
![Python](https://img.shields.io/badge/Python-3.10-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A real-time AI-based Vedic chanting analysis and feedback system. It captures voice input through a microphone, detects pitch using the **aubio YIN algorithm**, classifies Vedic Svaras, and provides instant AI feedback on chanting quality.

---

## 📋 Table of Contents

1. [System Architecture](#system-architecture)
2. [Project Structure](#project-structure)
3. [Prerequisites](#prerequisites)
4. [Installation and Build](#installation-and-build)
5. [Running the System](#running-the-system)
6. [ROS2 Topics](#ros2-topics)
7. [Vedic Swara Reference](#vedic-swara-reference)
8. [AI Feedback Logic](#ai-feedback-logic)
9. [Node Parameters](#node-parameters)
10. [Streamlit Dashboard](#streamlit-dashboard)
11. [Development Status](#development-status)
12. [Troubleshooting](#troubleshooting)
13. [Dependencies](#dependencies)

---

## 🏗️ System Architecture

Microphone Input
|
v
[audio_capture_node]
|
| /raw_audio (Float32MultiArray)
v
[pitch_analysis_node]
|
| /pitch_data (JSON)
v
[ai_feedback_node]
|
| /chanting_feedback (JSON)
|
+--------> [feedback_display_node] Terminal output
|
v
[ros2_redis_bridge]
|
v
Redis
|
v
[Streamlit Dashboard] → http://localhost:8501


---

## 🗂️ Project Structure

vedic_chanting_analyzer/
├── vedic_chanting_analyzer/
│ ├── _init_.py
│ ├── audio_capture_node.py
│ ├── pitch_analysis_node.py
│ ├── ai_feedback_node.py
│ ├── feedback_display_node.py
│ └── ros2_redis_bridge.py
├── launch/
│ └── vedic_analyzer.launch.py
├── resource/
│ └── vedic_chanting_analyzer
├── streamlit_dashboard.py
├── package.xml
├── setup.py
├── setup.cfg
├── requirements.txt
└── README.md

---

## ⚙️ Prerequisites

- Ubuntu 22.04
- ROS2 Humble
- Python 3.10+
- Redis Server

```bash
# Install Redis
sudo apt install redis-server
sudo systemctl enable redis
sudo systemctl start redis

# Install Python dependencies
pip install -r requirements.txt
```

---

## 🛠️ Installation and Build

```bash
# Clone the repository
cd ~/Documents/Projects/vedic_ws/src
git clone https://github.com/<your-username>/vedic_chanting_analyzer.git

# Source ROS2
source /opt/ros/humble/setup.bash

# Build the package
cd ~/Documents/Projects/vedic_ws
colcon build --packages-select vedic_chanting_analyzer

# Source the workspace
source install/setup.bash
```

---

## 🚀 Running the System

Open **4 separate terminals**:

**Terminal 1 — Launch all ROS2 nodes**
```bash
source ~/Documents/Projects/vedic_ws/install/setup.bash
ros2 launch vedic_chanting_analyzer vedic_analyzer.launch.py
```

**Terminal 2 — Start Redis**
```bash
sudo systemctl start redis
```

**Terminal 3 — Monitor topics (optional)**
```bash
source ~/Documents/Projects/vedic_ws/install/setup.bash
ros2 topic echo /pitch_data
ros2 topic echo /chanting_feedback
```

**Terminal 4 — Streamlit Dashboard**
```bash
cd ~/Documents/Projects/vedic_ws
streamlit run streamlit_dashboard.py
```
Open browser at **http://localhost:8501**

---

## 🔗 ROS2 Topics

| Topic | Type | Description |
|---|---|---|
| `/raw_audio` | `Float32MultiArray` | Raw microphone audio frames |
| `/pitch_data` | `String` (JSON) | Detected Hz, Swara, confidence, deviation |
| `/chanting_feedback` | `String` (JSON) | AI quality assessment and advice |

**`/pitch_data` example:**
```json
{
  "frequency_hz": 261.63,
  "confidence": 0.92,
  "detected_swara": "Sa",
  "deviation_cents": 8.5,
  "timestamp": 1234567890
}
```

**`/chanting_feedback` example:**
```json
{
  "status": "active",
  "dominant_swara": "Sa",
  "quality": "Excellent (Shuddha Swara)",
  "advice": "Perfect intonation. Maintain this level.",
  "accuracy_percent": 94.5,
  "pitch_trend": "Stable pitch - good intonation",
  "avg_deviation_cents": 9.2
}
```

---

## 🎼 Vedic Swara Reference

> Default tonic: **Sa = C4 = 261.63 Hz** — change via `tonic_hz` in `vedic_analyzer.launch.py`

| Swara | Type | Ratio | Frequency (Hz) |
|---|---|---|---|
| Sa   | Achala | 1/1      | 261.63 |
| Ri1  | Chala  | 256/243  | 275.62 |
| Ri2  | Chala  | 9/8      | 294.33 |
| Ga1  | Chala  | 32/27    | 309.03 |
| Ga2  | Chala  | 81/64    | 331.12 |
| Ga3  | Chala  | 5/4      | 327.03 |
| Ma1  | Chala  | 4/3      | 348.83 |
| Ma2  | Chala  | 45/32    | 367.92 |
| Pa   | Achala | 3/2      | 392.44 |
| Dha1 | Chala  | 128/81   | 413.43 |
| Dha2 | Chala  | 5/3      | 436.05 |
| Ni1  | Chala  | 16/9     | 465.12 |
| Ni3  | Chala  | 15/8     | 490.55 |

---

## 🤖 AI Feedback Logic

| Avg Deviation | Quality | Advice |
|---|---|---|
| < 15 cents   | ✅ Excellent (Shuddha Swara) | Maintain intonation |
| 15–30 cents  | 🟡 Good (minor variation)    | Focus on breath control |
| 30–50 cents  | 🟠 Needs improvement         | Slow down and retune |
| > 50 cents   | 🔴 Poor intonation           | Practice with tanpura |

- **Sa and Pa** (Achala — immovable): strict tolerance **±15 cents**
- **All others** (Chala — movable): tolerance **±25 cents**

---

## 🧩 Node Parameters

### audio_capture_node
| Parameter | Default | Description |
|---|---|---|
| `sample_rate` | 44100 | Audio sample rate (Hz) |
| `buffer_size` | 2048  | Frames per buffer |
| `channels`    | 1     | Mono input |

### pitch_analysis_node
| Parameter | Default | Description |
|---|---|---|
| `tonic_hz`    | 261.63 | Sa reference frequency |
| `sample_rate` | 44100  | Must match capture node |
| `buffer_size` | 2048   | Must match capture node |

### ai_feedback_node
| Parameter | Default | Description |
|---|---|---|
| `window_size`      | 30  | Smoothing window (frames) |
| `feedback_rate_hz` | 2.0 | Feedback publish rate (Hz) |

### ros2_redis_bridge
| Parameter | Default | Description |
|---|---|---|
| `redis_host` | localhost | Redis server host |
| `redis_port` | 6379      | Redis server port |

---

## 📊 Streamlit Dashboard

| Panel | Chart Type | Data Source |
|---|---|---|
| KPI Metrics Row    | `st.metric` cards     | `/latest_pitch`, `/latest_feedback` |
| Pitch Tracking     | Plotly line chart     | `pitch_history` Redis list |
| Swara Distribution | Plotly bar chart      | `pitch_history` aggregated |
| Deviation Gauge    | Plotly gauge          | `/chanting_feedback` |
| AI Feedback Card   | Styled HTML card      | `/chanting_feedback` |
| Session Log        | `st.dataframe`        | Rolling last 20 events |

---

## 📌 Development Status

### ✅ Completed
- [x] Microphone audio capture (PyAudio)
- [x] Real-time pitch detection (aubio YIN algorithm)
- [x] Vedic Swara classification (13 Svaras)
- [x] AI feedback with deviation and trend analysis
- [x] ROS2 pipeline (5 nodes)
- [x] Redis bridge for Streamlit integration
- [x] Real-time Streamlit dashboard with Plotly charts
- [x] Launch file for all nodes

### 🔧 In Progress / Planned
- [ ] DTW (Dynamic Time Warping) for mantra pattern matching
- [ ] Gamaka (ornamental oscillation) detection
- [ ] TTS voice feedback using `ros-humble-tts`
- [ ] PostgreSQL session history logging
- [ ] Grafana dashboard integration
- [ ] Mobile-friendly Streamlit layout
- [ ] Tonic auto-detection from first 3 seconds of input

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| `No module named aubio` | `pip install aubio pyaudio` |
| `No module named vedic_chanting_analyzer` | Node files must be inside `vedic_chanting_analyzer/` folder, **not** `scripts/` |
| `streamlit_dashboard.py not found` | `cd ~/Documents/Projects/vedic_ws` then run streamlit |
| Redis connection refused | `sudo systemctl start redis` then `redis-cli ping` (must return PONG) |
| Dashboard shows Waiting for ROS2 | Run `ros2 topic list` — `/pitch_data` and `/chanting_feedback` must appear |
| colcon build fails | `rm -rf build/ install/ log/` then rebuild fresh |

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `aubio`       | >=0.4.9  | Pitch detection (YIN algorithm) |
| `pyaudio`     | >=0.2.13 | Microphone audio capture |
| `librosa`     | >=0.10.0 | Audio analysis utilities |
| `numpy`       | >=1.24.0 | Numerical processing |
| `scipy`       | >=1.10.0 | Signal processing |
| `sounddevice` | >=0.4.6  | Audio I/O |
| `redis`       | >=4.6.0  | ROS2 to Streamlit bridge |
| `streamlit`   | >=1.32.0 | Live dashboard framework |
| `plotly`      | >=5.18.0 | Interactive charts |
| `pandas`      | >=2.0.0  | Data manipulation |

---

## 📄 License

MIT License

Copyright (c) 2026 Bhanu Teja Vadlamudi
Master's Student — Autonomous Driving, Hochschule Coburg, Germany

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in ALL
copies or substantial portions of the Software.

ATTRIBUTION NOTICE:
If you use, modify, or build upon this project, you are kindly requested to
give credit to the original author:

    Bhanu Teja Vadlamudi
    Master's Student — Autonomous Driving
    Hochschule Coburg, Germany
    GitHub: https://github.com/<tejavadlamudi03>

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## 👤 Author

**Bhanu**
Master's Student — Autonomous Driving, Hochschule Coburg
AI-assisted Robotics and Speech Processing Research

## 🙏 Attribution

If you use, modify, fork, or build upon this project in any way,
please give credit to the original author:

**Bhanu Teja Vadlamudi**
Master's Student — Autonomous Driving
Hochschule Coburg, Germany
GitHub: https://github.com/<tejavadlamudi03>

You are free to use this project under the MIT License,
but a mention or credit is greatly appreciated. 🙏

---

> © 2026 Bhanu Teja Vadlamudi. Built as part of AI-assisted
