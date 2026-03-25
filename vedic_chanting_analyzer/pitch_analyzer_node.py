#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import pyaudio
import numpy as np
import aubio

from vedic_chanting_analyzer_msgs.msg import PitchData

# Vedic swara frequencies (Hz) based on Sa = 261.63 Hz (C4)
SWARA_FREQUENCIES = {
    'Sa':  261.63,
    'Re':  293.66,
    'Ga':  329.63,
    'Ma':  349.23,
    'Pa':  392.00,
    'Dha': 440.00,
    'Ni':  493.88,
}

class PitchAnalyzerNode(Node):
    def __init__(self):
        super().__init__('pitch_analyzer_node')

        # Parameters
        self.declare_parameter('sample_rate', 44100)
        self.declare_parameter('buffer_size', 1024)
        self.declare_parameter('confidence_threshold', 0.8)

        self.sample_rate = self.get_parameter('sample_rate').value
        self.buffer_size = self.get_parameter('buffer_size').value
        self.confidence_threshold = self.get_parameter('confidence_threshold').value

        # Publisher
        self.publisher = self.create_publisher(PitchData, '/vedic/pitch_data', 10)

        # Aubio pitch detector
        self.pitch_detector = aubio.pitch(
            "yin",
            self.buffer_size * 2,
            self.buffer_size,
            self.sample_rate
        )
        self.pitch_detector.set_unit("Hz")
        self.pitch_detector.set_confidence_threshold(self.confidence_threshold)

        # PyAudio stream
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.buffer_size,
            stream_callback=self.audio_callback
        )

        self.get_logger().info('🎵 Pitch Analyzer Node started!')
        self.get_logger().info(f'Sample rate: {self.sample_rate} Hz, Buffer: {self.buffer_size}')

    def audio_callback(self, in_data, frame_count, time_info, status):
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        frequency = self.pitch_detector(audio_data)[0]
        confidence = self.pitch_detector.get_confidence()

        if frequency > 50.0 and confidence > self.confidence_threshold:
            swara, deviation = self.detect_swara(frequency)
            self.publish_pitch(frequency, confidence, swara, deviation)

        return (in_data, pyaudio.paContinue)

    def detect_swara(self, frequency):
        """Find the closest Vedic swara and deviation in cents."""
        closest_swara = None
        min_deviation = float('inf')

        for swara, ref_freq in SWARA_FREQUENCIES.items():
            # Deviation in cents: 1200 * log2(f/f_ref)
            deviation = 1200 * np.log2(frequency / ref_freq)
            if abs(deviation) < abs(min_deviation):
                min_deviation = deviation
                closest_swara = swara

        return closest_swara, min_deviation

    def publish_pitch(self, frequency, confidence, swara, deviation):
        msg = PitchData()
        msg.frequency_hz = float(frequency)
        msg.confidence = float(confidence)
        msg.detected_swara = swara
        msg.deviation_cents = float(deviation)
        msg.stamp = self.get_clock().now().to_msg()

        self.publisher.publish(msg)
        self.get_logger().info(
            f'Swara: {swara} | Freq: {frequency:.2f} Hz | '
            f'Deviation: {deviation:.1f} cents | Confidence: {confidence:.2f}'
        )

    def destroy_node(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PitchAnalyzerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down Pitch Analyzer...')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
