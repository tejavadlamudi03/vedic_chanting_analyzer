import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import pyaudio
import numpy as np

class AudioCaptureNode(Node):
    def __init__(self):
        super().__init__('audio_capture_node')
        
        # Parameters
        self.declare_parameter('sample_rate', 44100)
        self.declare_parameter('buffer_size', 2048)
        self.declare_parameter('channels', 1)
        
        self.sample_rate = self.get_parameter('sample_rate').value
        self.buffer_size = self.get_parameter('buffer_size').value
        self.channels    = self.get_parameter('channels').value
        
        self.publisher_ = self.create_publisher(Float32MultiArray, '/raw_audio', 10)
        
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(
            format=pyaudio.paFloat32,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.buffer_size,
            stream_callback=self.audio_callback
        )
        self.stream.start_stream()
        self.get_logger().info('Audio Capture Node started. Listening to microphone...')

    def audio_callback(self, in_data, frame_count, time_info, status):
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        msg = Float32MultiArray()
        msg.data = audio_data.tolist()
        self.publisher_.publish(msg)
        return (in_data, pyaudio.paContinue)

    def destroy_node(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = AudioCaptureNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
