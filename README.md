
=======================================================
        VEDIC CHANTING ANALYZER - ROS2 PROJECT
=======================================================

  ⚠️  NOTE: This project is currently under active
      development. Features may be incomplete or
      subject to change. Contributions and feedback
      are welcome.

=======================================================

A real-time AI-based Vedic chanting analysis and feedback
system built with ROS2 (Humble), Python, aubio pitch
detection, Redis, and a Streamlit dashboard.

-------------------------------------------------------
SYSTEM OVERVIEW
-------------------------------------------------------

Microphone Input
      |
[audio_capture_node]  --> /raw_audio --> [pitch_analysis_node]
                                                |
                                        /pitch_data --> [ai_feedback_node]
                                                                |
                                                  /chanting_feedback
                                                                |
                                                  [ros2_redis_bridge]
                                                                |
                                                             Redis
                                                                |
                                                  [Streamlit Dashboard]
                                                  http://localhost:8501

-------------------------------------------------------
PROJECT STRUCTURE
-------------------------------------------------------

vedic_chanting_analyzer/
├── vedic_chanting_analyzer/
│   ├── __init__.py
│   ├── audio_capture_node.py
│   ├── pitch_analysis_node.py
│   ├── ai_feedback_node.py
│   ├── feedback_display_node.py
│   └── ros2_redis_bridge.py
├── launch/
│   └── vedic_analyzer.launch.py
├── resource/
│   └── vedic_chanting_analyzer
├── streamlit_dashboard.py
├── package.xml
├── setup.py
├── setup.cfg
├── requirements.txt
└── README.txt

-------------------------------------------------------
PREREQUISITES
-------------------------------------------------------

- Ubuntu 22.04
- ROS2 Humble
- Python 3.10+
- Redis Server

Install Redis:
  sudo apt install redis-server
  sudo systemctl enable redis
  sudo systemctl start redis

Install Python dependencies:
  pip install -r requirements.txt

-------------------------------------------------------
BUILD INSTRUCTIONS
-------------------------------------------------------

  cd ~/Documents/Projects/vedic_ws
  source /opt/ros/humble/setup.bash
  colcon build --packages-select vedic_chanting_analyzer
  source install/setup.bash

-------------------------------------------------------
RUNNING THE SYSTEM
-------------------------------------------------------

Terminal 1 - Launch all ROS2 nodes:
  source ~/Documents/Projects/vedic_ws/install/setup.bash
  ros2 launch vedic_chanting_analyzer vedic_analyzer.launch.py

Terminal 2 - Start Redis:
  sudo systemctl start redis

Terminal 3 - Monitor topics (optional):
  ros2 topic echo /pitch_data
  ros2 topic echo /chanting_feedback

Terminal 4 - Streamlit Dashboard:
  cd ~/Documents/Projects/vedic_ws
  streamlit run streamlit_dashboard.py
  Open: http://localhost:8501

-------------------------------------------------------
ROS2 TOPICS
-------------------------------------------------------

/raw_audio          std_msgs/Float32MultiArray  Raw mic audio
/pitch_data         std_msgs/String (JSON)      Hz, Swara, confidence
/chanting_feedback  std_msgs/String (JSON)      AI feedback & advice

/pitch_data JSON:
{
  "frequency_hz": 261.63,
  "confidence": 0.92,
  "detected_swara": "Sa",
  "deviation_cents": 8.5,
  "timestamp": 1234567890
}

/chanting_feedback JSON:
{
  "status": "active",
  "dominant_swara": "Sa",
  "quality": "Excellent (Shuddha Swara)",
  "advice": "Perfect intonation. Maintain this level.",
  "accuracy_percent": 94.5,
  "pitch_trend": "Stable pitch - good intonation",
  "avg_deviation_cents": 9.2
}

-------------------------------------------------------
VEDIC SWARA REFERENCE  (Sa = C4 = 261.63 Hz)
-------------------------------------------------------

Swara   Ratio      Hz
------  ---------  --------
Sa      1/1        261.63
Ri1     256/243    275.62
Ri2     9/8        294.33
Ga1     32/27      309.03
Ga3     5/4        327.03
Ma1     4/3        348.83
Ma2     45/32      367.92
Pa      3/2        392.44
Dha2    5/3        436.05
Ni3     15/8       490.55

Change tonic by editing tonic_hz in vedic_analyzer.launch.py

-------------------------------------------------------
AI FEEDBACK LOGIC
-------------------------------------------------------

Deviation       Quality                   Action
-----------     ------------------------  --------------------
< 15 cents      Excellent (Shuddha Swara) Maintain intonation
15 to 30 cents  Good (minor variation)    Focus on breath control
30 to 50 cents  Needs improvement         Slow down and retune
> 50 cents      Poor intonation           Practice with tanpura

Sa and Pa (Achala) : strict tolerance +/- 15 cents
All others (Chala) : tolerance +/- 25 cents

-------------------------------------------------------
NODE PARAMETERS
-------------------------------------------------------

audio_capture_node:
  sample_rate  44100    Audio sample rate (Hz)
  buffer_size  2048     Frames per buffer
  channels     1        Mono input

pitch_analysis_node:
  tonic_hz     261.63   Sa reference frequency
  sample_rate  44100
  buffer_size  2048

ai_feedback_node:
  window_size       30   Smoothing window (frames)
  feedback_rate_hz  2.0  Feedback publish rate

ros2_redis_bridge:
  redis_host  localhost
  redis_port  6379

-------------------------------------------------------
TROUBLESHOOTING
-------------------------------------------------------

No module named aubio:
  pip install aubio pyaudio

No module named vedic_chanting_analyzer:
  ls ~/Documents/Projects/vedic_ws/src/vedic_chanting_analyzer/vedic_chanting_analyzer/
  (all node .py files must be inside this folder, NOT scripts/)

streamlit_dashboard.py not found:
  cd ~/Documents/Projects/vedic_ws
  streamlit run streamlit_dashboard.py

Redis connection refused:
  sudo systemctl start redis
  redis-cli ping   (should return PONG)

Dashboard shows "Waiting for ROS2":
  ros2 topic list
  (/pitch_data and /chanting_feedback must appear)

-------------------------------------------------------
PYTHON DEPENDENCIES
-------------------------------------------------------

aubio>=0.4.9
pyaudio>=0.2.13
librosa>=0.10.0
numpy>=1.24.0
scipy>=1.10.0
sounddevice>=0.4.6
redis>=4.6.0
streamlit>=1.32.0
plotly>=5.18.0
pandas>=2.0.0

-------------------------------------------------------
DEVELOPMENT STATUS
-------------------------------------------------------

  This project is currently under active development.
  The following features are planned or in progress:

  [DONE]
  - Audio capture via microphone (PyAudio)
  - Real-time pitch detection (aubio YIN algorithm)
  - Vedic Swara classification (13 Svaras)
  - AI-based feedback with deviation analysis
  - ROS2 topic pipeline (4 nodes)
  - Redis bridge for data streaming
  - Streamlit real-time dashboard

  [IN PROGRESS / PLANNED]
  - DTW (Dynamic Time Warping) for mantra pattern matching
  - Gamaka (ornamental oscillation) detection
  - TTS voice feedback using ros-humble-tts
  - PostgreSQL session history logging
  - Grafana dashboard integration
  - Mobile-friendly Streamlit layout

-------------------------------------------------------
LICENSE
-------------------------------------------------------

MIT License

-------------------------------------------------------
AUTHOR
-------------------------------------------------------

Bhanu
Master's Student - Autonomous Driving, Hochschule Coburg
AI-assisted robotics and speech processing research.

=======================================================
