import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import numpy as np
from collections import deque

class AIFeedbackNode(Node):
    
    # Vedic chanting rules: acceptable deviation per swara (cents)
    SWARA_TOLERANCE = {
        'Sa': 15, 'Pa': 15,           # Achala (immovable) — strictest
        'Ri1': 25, 'Ri2': 25,
        'Ga1': 25, 'Ga2': 25, 'Ga3': 25,
        'Ma1': 25, 'Ma2': 25,
        'Dha1': 25, 'Dha2': 25,
        'Ni1': 25, 'Ni2': 25, 'Ni3': 25,
    }

    def __init__(self):
        super().__init__('ai_feedback_node')
        
        self.declare_parameter('window_size', 30)      # frames for smoothing
        self.declare_parameter('feedback_rate_hz', 2.0)
        
        self.window_size = self.get_parameter('window_size').value
        
        self.pitch_buffer = deque(maxlen=self.window_size)
        self.swara_buffer = deque(maxlen=self.window_size)
        self.session_stats = {'correct': 0, 'total': 0, 'errors': []}
        
        self.subscription = self.create_subscription(
            String, '/pitch_data', self.pitch_callback, 10)
        self.feedback_pub = self.create_publisher(String, '/chanting_feedback', 10)
        
        timer_period = 1.0 / self.get_parameter('feedback_rate_hz').value
        self.timer = self.create_timer(timer_period, self.publish_feedback)
        
        self.get_logger().info('AI Feedback Node ready.')

    def pitch_callback(self, msg):
        data = json.loads(msg.data)
        if data['confidence'] > 0.7 and data['detected_swara'] != 'Silence':
            self.pitch_buffer.append(data['frequency_hz'])
            self.swara_buffer.append({
                'swara': data['detected_swara'],
                'deviation': data['deviation_cents']
            })
            self.session_stats['total'] += 1
            
            tolerance = self.SWARA_TOLERANCE.get(data['detected_swara'], 30)
            if data['deviation_cents'] <= tolerance:
                self.session_stats['correct'] += 1
            else:
                self.session_stats['errors'].append({
                    'swara': data['detected_swara'],
                    'deviation': data['deviation_cents']
                })

    def analyze_trend(self):
        if len(self.pitch_buffer) < 5:
            return "Insufficient data"
        
        pitches = list(self.pitch_buffer)
        trend = np.polyfit(range(len(pitches)), pitches, 1)[0]
        
        if abs(trend) < 0.1:
            return "Stable pitch — good intonation"
        elif trend > 0.5:
            return "Pitch drifting upward (Shruti rising)"
        elif trend < -0.5:
            return "Pitch drifting downward (Shruti falling)"
        return "Minor pitch variation — acceptable"

    def generate_feedback(self):
        if not self.swara_buffer:
            return {"status": "waiting", "message": "Start chanting..."}
        
        recent = list(self.swara_buffer)[-10:]
        avg_deviation = np.mean([r['deviation'] for r in recent])
        swara_counts = {}
        for r in recent:
            swara_counts[r['swara']] = swara_counts.get(r['swara'], 0) + 1
        
        dominant_swara = max(swara_counts, key=swara_counts.get)
        accuracy = (self.session_stats['correct'] / max(self.session_stats['total'], 1)) * 100
        
        # AI rule-based assessment
        if avg_deviation < 15:
            quality = "Excellent (Shuddha Swara)"
            advice = "Perfect intonation. Maintain this level."
        elif avg_deviation < 30:
            quality = "Good (minor variation)"
            advice = f"Slight deviation in {dominant_swara}. Focus on breath control."
        elif avg_deviation < 50:
            quality = "Needs improvement"
            advice = f"{dominant_swara} is off by {avg_deviation:.1f} cents. Slow down and tune."
        else:
            quality = "Poor intonation"
            advice = f"Large deviation ({avg_deviation:.1f} cents). Practice {dominant_swara} with tanpura reference."
        
        return {
            "status": "active",
            "dominant_swara": dominant_swara,
            "quality": quality,
            "advice": advice,
            "accuracy_percent": round(accuracy, 1),
            "pitch_trend": self.analyze_trend(),
            "avg_deviation_cents": round(avg_deviation, 2)
        }

    def publish_feedback(self):
        feedback = self.generate_feedback()
        msg = String()
        msg.data = json.dumps(feedback)
        self.feedback_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = AIFeedbackNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
