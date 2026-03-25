from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

def generate_launch_description():
    return LaunchDescription([

        # ROS2 Nodes
        Node(
            package='vedic_chanting_analyzer',
            executable='audio_capture_node',
            name='audio_capture',
            parameters=[{'sample_rate': 44100, 'buffer_size': 2048}]
        ),

        Node(
            package='vedic_chanting_analyzer',
            executable='pitch_analysis_node',
            name='pitch_analysis',
            parameters=[{'tonic_hz': 261.63}]
        ),

        Node(
            package='vedic_chanting_analyzer',
            executable='ai_feedback_node',
            name='ai_feedback',
            parameters=[{'window_size': 30, 'feedback_rate_hz': 2.0}]
        ),

        Node(
            package='vedic_chanting_analyzer',
            executable='feedback_display_node',
            name='feedback_display'
        ),

        Node(
            package='vedic_chanting_analyzer',
            executable='ros2_streamlit_bridge',
            name='streamlit_bridge'
        ),

        # Streamlit Dashboard
        ExecuteProcess(
            cmd=[
                'streamlit', 'run',
                '/home/bhanu/vedic_ws/src/vedic_chanting_analyzer/'
                'vedic_chanting_analyzer/dashboard.py',
                '--server.port', '8501',
                '--server.headless', 'true'
            ],
            output='screen'
        ),
    ])

