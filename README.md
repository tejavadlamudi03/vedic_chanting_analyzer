=======================================================
        VEDIC CHANTING ANALYZER - ROS2 PROJECT
=======================================================

  STATUS: Under Active Development
  Version: 0.1.0
  Author:  Bhanu
  License: MIT

=======================================================
TABLE OF CONTENTS
=======================================================

  1. Project Description
  2. System Architecture
  3. Project Structure
  4. Prerequisites
  5. Installation and Build
  6. Running the System
  7. ROS2 Topics
  8. Vedic Swara Reference
  9. AI Feedback Logic
  10. Node Parameters
  11. Streamlit Dashboard
  12. Development Status
  13. Troubleshooting
  14. Dependencies

=======================================================
1. PROJECT DESCRIPTION
=======================================================

  A real-time AI-based Vedic chanting analysis and
  feedback system. It captures voice input through a
  microphone, detects pitch using the aubio YIN
  algorithm, classifies Vedic Svaras, and provides
  instant AI feedback on chanting quality.

  Built With:
    - ROS2 Humble (robot middleware framework)
    - Python 3.10
    - aubio (pitch detection)
    - Redis (data bridge)
    - Streamlit + Plotly (live dashboard)

=======================================================
2. SYSTEM ARCHITECTURE
=======================================================

  Microphone
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
      +--------> [feedback_display_node]  (terminal)
      |
      v
  [ros2_redis_bridge]
      |
      v
    Redis
      |
      v
  [Streamlit Dashboard]
  http://localhost:8501

=======================================================
3. PROJECT STRUCTURE
=======================================================

  vedic_chanting_analyzer/
  |
  |-- vedic_chanting_analyzer/       (Python module)
  |   |-- __init__.py
  |   |-- audio_capture_node.py
  |   |-- pitch_analysis_node.py
  |   |-- ai_feedback_node.py
  |   |-- feedback_display_node.py
  |   |-- ros2_redis_bridge.py
  |
  |-- launch/
  |   |-- vedic_analyzer.launch.py
  |
  |-- resource/
  |   |-- vedic_chanting_analyzer
  |
  |-- streamlit_dashboard.py
  |-- package.xml
  |-- setup.py
  |-- setup.cfg
  |-- requirements.txt
  |-- README.txt

=======================================================
4. PREREQUISITES
=======================================================

  Operating System : Ubuntu 22.04
  ROS2 Version     : Humble Hawksbill
  Python Version   : 3.10+
  Redis Server     : Required for Streamlit bridge

  Install Redis:
    sudo apt install redis-server
    sudo systemctl enable redis
    sudo systemctl start redis

  Install Python packages:
    pip install -r requirements.txt

=======================================================
5. INSTALLATION AND BUILD
=======================================================

  Step 1 - Clone the repository:
    cd ~/Documents/Projects/vedic_ws/src
    git clone https://github.com/<your-username>/vedic_chanting_analyzer.git

  Step 2 - Source ROS2:
    source /opt/ros/humble/setup.bash

  Step 3 - Build the package:
    cd ~/Documents/Projects/vedic_ws
    colcon build --packages-select vedic_chanting_analyzer

  Step 4 - Source the workspace:
    source install/setup.bash

=======================================================
6. RUNNING THE SYSTEM
=======================================================

  Open 4 separate terminals and run:

  Terminal 1 - ROS2 Nodes:
    source ~/Documents/Projects/vedic_ws/install/setup.bash
    ros2 launch vedic_chanting_analyzer vedic_analyzer.launch.py

  Terminal 2 - Redis Server:
    sudo systemctl start redis

  Terminal 3 - Monitor Topics (optional):
    source ~/Documents/Projects/vedic_ws/install/setup.bash
    ros2 topic echo /pitch_data
    ros2 topic echo /chanting_feedback

  Terminal 4 - Streamlit Dashboard:
    cd ~/Documents/Projects/vedic_ws
    streamlit run streamlit_dashboard.py
    Open browser: http://localhost:8501

=======================================================
7. ROS2 TOPICS
=======================================================

  Topic                 Type                        Description
  --------------------  --------------------------  -------------------
  /raw_audio            Float32MultiArray           Raw mic audio frames
  /pitch_data           String (JSON)               Hz, Swara, confidence
  /chanting_feedback    String (JSON)               AI feedback and advice

  /pitch_data JSON example:
  {
    "frequency_hz"   : 261.63,
    "confidence"     : 0.92,
    "detected_swara" : "Sa",
    "deviation_cents": 8.5,
    "timestamp"      : 1234567890
  }

  /chanting_feedback JSON example:
  {
    "status"              : "active",
    "dominant_swara"      : "Sa",
    "quality"             : "Excellent (Shuddha Swara)",
    "advice"              : "Perfect intonation. Maintain this level.",
    "accuracy_percent"    : 94.5,
    "pitch_trend"         : "Stable pitch - good intonation",
    "avg_deviation_cents" : 9.2
  }

=======================================================
8. VEDIC SWARA REFERENCE  (Default: Sa = C4 = 261.63 Hz)
=======================================================

  Swara    Type      Ratio      Frequency (Hz)
  -------  --------  ---------  --------------
  Sa       Achala    1/1        261.63
  Ri1      Chala     256/243    275.62
  Ri2      Chala     9/8        294.33
  Ga1      Chala     32/27      309.03
  Ga2      Chala     81/64      331.12
  Ga3      Chala     5/4        327.03
  Ma1      Chala     4/3        348.83
  Ma2      Chala     45/32      367.92
  Pa       Achala    3/2        392.44
  Dha1     Chala     128/81     413.43
  Dha2     Chala     5/3        436.05
  Ni1      Chala     16/9       465.12
  Ni3      Chala     15/8       490.55

  Note: Change tonic by editing tonic_hz parameter
        in launch/vedic_analyzer.launch.py

=======================================================
9. AI FEEDBACK LOGIC
=======================================================

  Deviation         Quality Label              Advice
  ---------------   ------------------------   ----------------------
  Less than 15 c    Excellent (Shuddha Swara)  Maintain intonation
  15 to 30 cents    Good (minor variation)     Focus on breath control
  30 to 50 cents    Needs improvement          Slow down and retune
  More than 50 c    Poor intonation            Practice with tanpura

  Tolerance Rules:
    Sa and Pa  (Achala - immovable)  : +/- 15 cents  (strict)
    All others (Chala  - movable)    : +/- 25 cents  (relaxed)

=======================================================
10. NODE PARAMETERS
=======================================================

  audio_capture_node:
    sample_rate   44100     Audio sample rate in Hz
    buffer_size   2048      Frames per audio buffer
    channels      1         Mono microphone input

  pitch_analysis_node:
    tonic_hz      261.63    Sa reference frequency in Hz
    sample_rate   44100     Must match audio_capture_node
    buffer_size   2048      Must match audio_capture_node

  ai_feedback_node:
    window_size       30    Smoothing window in frames
    feedback_rate_hz  2.0   Feedback publish rate in Hz

  ros2_redis_bridge:
    redis_host    localhost  Redis server hostname
    redis_port    6379       Redis server port

=======================================================
11. STREAMLIT DASHBOARD PANELS
=======================================================

  Panel               Type                  Data Source
  ------------------  --------------------  ----------------------
  KPI Metrics Row     st.metric cards       /latest_pitch
  Pitch Tracking      Plotly line chart     pitch_history (Redis)
  Swara Distribution  Plotly bar chart      pitch_history (Redis)
  Deviation Gauge     Plotly gauge          /chanting_feedback
  AI Feedback Card    HTML styled card      /chanting_feedback
  Session Log Table   st.dataframe          Rolling 20 events

=======================================================
12. DEVELOPMENT STATUS
=======================================================

  COMPLETED:
    [x] Microphone audio capture (PyAudio)
    [x] Real-time pitch detection (aubio YIN algorithm)
    [x] Vedic Swara classification (13 Svaras)
    [x] AI feedback with deviation and trend analysis
    [x] ROS2 pipeline (5 nodes)
    [x] Redis bridge for Streamlit integration
    [x] Real-time Streamlit dashboard with Plotly charts
    [x] Launch file for all nodes

  IN PROGRESS / PLANNED:
    [ ] DTW (Dynamic Time Warping) for mantra pattern matching
    [ ] Gamaka (ornamental oscillation) detection
    [ ] TTS voice feedback (ros-humble-tts)
    [ ] PostgreSQL session history logging
    [ ] Grafana dashboard integration
    [ ] Mobile-friendly Streamlit layout
    [ ] Tonic auto-detection from first 3 seconds

=======================================================
13. TROUBLESHOOTING
=======================================================

  Problem  : No module named aubio
  Solution : pip install aubio pyaudio

  Problem  : No module named vedic_chanting_analyzer
  Solution : Node files must be inside the module folder
             ls .../vedic_chanting_analyzer/vedic_chanting_analyzer/
             (NOT inside a scripts/ folder)

  Problem  : streamlit_dashboard.py not found
  Solution : cd ~/Documents/Projects/vedic_ws
             streamlit run streamlit_dashboard.py

  Problem  : Redis connection refused
  Solution : sudo systemctl start redis
             redis-cli ping   (must return PONG)

  Problem  : Dashboard shows "Waiting for ROS2"
  Solution : ros2 topic list
             /pitch_data and /chanting_feedback must appear

  Problem  : colcon build fails with "package does not exist"
  Solution : rm -rf build/ install/ log/
             source /opt/ros/humble/setup.bash
             colcon build --packages-select vedic_chanting_analyzer

=======================================================
14. PYTHON DEPENDENCIES
=======================================================

  Package       Version    Purpose
  -----------   ---------  --------------------------
  aubio         >=0.4.9    Pitch detection (YIN)
  pyaudio       >=0.2.13   Microphone audio capture
  librosa       >=0.10.0   Audio analysis utilities
  numpy         >=1.24.0   Numerical processing
  scipy         >=1.10.0   Signal processing
  sounddevice   >=0.4.6    Audio I/O
  redis         >=4.6.0    ROS2 to Streamlit bridge
  streamlit     >=1.32.0   Live dashboard framework
  plotly        >=5.18.0   Interactive charts
  pandas        >=2.0.0    Data manipulation

=======================================================
  Bhanu | Master's in Autonomous Driving | Hochschule Coburg
  AI-assisted Robotics and Speech Processing Research
=======================================================
