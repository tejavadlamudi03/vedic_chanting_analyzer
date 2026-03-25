#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json

class StreamlitBridge(Node):
    def __init__(self):
        super().__init__('streamlit_bridge')
        
        self.create_subscription(
            String, '/pitch_data',
            self.pitch_cb, 10)
        
        self.create_subscription(
            String, '/chanting_feedback',
            self.feedback_cb, 10)
        
        self.get_logger().info('Streamlit bridge running...')

    def pitch_cb(self, msg):
        with open('/tmp/vedic_pitch.json', 'w') as f:
            f.write(msg.data)

    def feedback_cb(self, msg):
        with open('/tmp/vedic_feedback.json', 'w') as f:
            f.write(msg.data)

def main(args=None):
    rclpy.init(args=args)
    node = StreamlitBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
