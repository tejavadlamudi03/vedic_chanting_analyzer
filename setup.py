from setuptools import setup
import os
from glob import glob

package_name = 'vedic_chanting_analyzer'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='bhanuteja',
    maintainer_email='bhanu.drive1@gmail.com',
    description='Vedic Chanting Analyzer',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'audio_capture_node = vedic_chanting_analyzer.audio_capture_node:main',
            'pitch_analysis_node = vedic_chanting_analyzer.pitch_analysis_node:main',
            'ai_feedback_node = vedic_chanting_analyzer.ai_feedback_node:main',
            'feedback_display_node = vedic_chanting_analyzer.feedback_display_node:main',
            'ros2_redis_bridge = vedic_chanting_analyzer.ros2_redis_bridge:main',
            'ros2_streamlit_bridge = vedic_chanting_analyzer.ros2_streamlit_bridge:main',

            

        ],
    },
)
