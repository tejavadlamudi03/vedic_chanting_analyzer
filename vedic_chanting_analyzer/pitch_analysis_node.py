import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, String
import aubio
import numpy as np
import json

class PitchAnalysisNode(Node):
    
    # Vedic Swara reference frequencies (Sa = C4 = 261.63 Hz as tonic)
    SWARA_RATIOS = {
        'Sa':  1.0,
        'Ri1': 256/243,  'Ri2': 9/8,
        'Ga1': 32/27,    'Ga2': 81/64,   'Ga3': 5/4,
        'Ma1': 4/3,      'Ma2': 45/32,
        'Pa':  3/2,
        'Dha1':128/81,   'Dha2': 5/3,
        'Ni1': 16/9,     'Ni2': 243/128, 'Ni3': 15/8,
    }

    def __init__(self):
        super().__init__('pitch_analysis_node')
        
        self.declare_parameter('sample_rate', 44100)
        self.declare_parameter('buffer_size', 2048)
        self.declare_parameter('tonic_hz', 261.63)  # Sa = C4 by default
        
        self.sample_rate = self.get_parameter('sample_rate').value
        self.buffer_size = self.get_parameter('buffer_size').value
        self.tonic_hz    = self.get_parameter('tonic_hz').value
        
        self.hop_size = self.buffer_size // 2
        
        # Aubio pitch detector
        self.pitch_detector = aubio.pitch(
            "yin",           # YIN algorithm — most accurate for voice
            self.buffer_size,
            self.hop_size,
            self.sample_rate
        )
        self.pitch_detector.set_unit("Hz")
        self.pitch_detector.set_silence(-35)
        self.pitch_detector.set_tolerance(0.8)
        
        self.subscription = self.create_subscription(
            Float32MultiArray, '/raw_audio', self.audio_callback, 10)
        self.publisher_ = self.create_publisher(String, '/pitch_data', 10)
        
        self.get_logger().info(f'Pitch Analysis Node ready. Tonic: {self.tonic_hz} Hz')

    def hz_to_cents(self, freq_hz, reference_hz):
        if freq_hz <= 0 or reference_hz <= 0:
            return 0.0
        return 1200.0 * np.log2(freq_hz / reference_hz)

    def classify_swara(self, freq_hz):
        if freq_hz < 60:
            return "Silence", 0.0
        
        # Normalize to tonic octave
        ratio = freq_hz / self.tonic_hz
        while ratio > 2.0:
            ratio /= 2.0
        while ratio < 1.0:
            ratio *= 2.0

        best_swara = "Unknown"
        min_cent_diff = float('inf')
        
        for swara, ref_ratio in self.SWARA_RATIOS.items():
            ref_hz = self.tonic_hz * ref_ratio
            cents_diff = abs(self.hz_to_cents(freq_hz, ref_hz))
            if cents_diff < min_cent_diff:
                min_cent_diff = cents_diff
                best_swara = swara

        return best_swara, min_cent_diff

    def audio_callback(self, msg):
        samples = np.array(msg.data, dtype=aubio.float_type)
        
        if len(samples) < self.hop_size:
            return
        
        pitch_hz = self.pitch_detector(samples[:self.hop_size])[0]
        confidence = self.pitch_detector.get_confidence()
        
        swara, deviation_cents = self.classify_swara(pitch_hz)
        
        pitch_data = {
            'frequency_hz': float(pitch_hz),
            'confidence': float(confidence),
            'detected_swara': swara,
            'deviation_cents': float(deviation_cents),
            'timestamp': self.get_clock().now().nanoseconds
        }
        
        out_msg = String()
        out_msg.data = json.dumps(pitch_data)
        self.publisher_.publish(out_msg)

def main(args=None):
    rclpy.init(args=args)
    node = PitchAnalysisNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
