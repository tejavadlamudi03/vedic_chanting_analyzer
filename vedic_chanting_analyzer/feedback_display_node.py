import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import os

class FeedbackDisplayNode(Node):
    def __init__(self):
        super().__init__('feedback_display_node')
        self.subscription = self.create_subscription(
            String, '/chanting_feedback', self.feedback_callback, 10)
        self.get_logger().info('Feedback Display Node active. Waiting for chanting...')

    def feedback_callback(self, msg):
        data = json.loads(msg.data)
        if data['status'] == 'waiting':
            return
        
        os.system('clear')
        print("=" * 55)
        print("       🕉  VEDIC CHANTING ANALYSIS SYSTEM  🕉")
        print("=" * 55)
        print(f"  Current Swara   : {data.get('dominant_swara', 'N/A')}")
        print(f"  Quality         : {data.get('quality', 'N/A')}")
        print(f"  Avg Deviation   : {data.get('avg_deviation_cents', 0)} cents")
        print(f"  Session Accuracy: {data.get('accuracy_percent', 0)}%")
        print(f"  Pitch Trend     : {data.get('pitch_trend', 'N/A')}")
        print("-" * 55)
        print(f"  Advice: {data.get('advice', '')}")
        print("=" * 55)

def main(args=None):
    rclpy.init(args=args)
    node = FeedbackDisplayNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
