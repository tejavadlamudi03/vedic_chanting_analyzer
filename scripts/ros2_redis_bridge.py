import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import redis
import json

class ROS2RedisBridge(Node):
    def __init__(self):
        super().__init__('ros2_redis_bridge')
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        self.create_subscription(String, '/pitch_data',       self.pitch_cb,    10)
        self.create_subscription(String, '/chanting_feedback',self.feedback_cb, 10)
        
        self.get_logger().info('ROS2 → Redis Bridge active.')

    def pitch_cb(self, msg):
        data = json.loads(msg.data)
        # Push to a Redis list (keep last 200 entries for history)
        self.redis_client.lpush('pitch_history', json.dumps(data))
        self.redis_client.ltrim('pitch_history', 0, 199)
        # Also store latest as a simple key
        self.redis_client.set('latest_pitch', msg.data)

    def feedback_cb(self, msg):
        self.redis_client.set('latest_feedback', msg.data)

def main(args=None):
    rclpy.init(args=args)
    node = ROS2RedisBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
