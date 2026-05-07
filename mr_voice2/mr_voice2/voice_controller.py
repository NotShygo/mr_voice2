import rclpy
from rclpy.node import Node
from mr_voice2.msg import Voice

class VoiceController(Node):
    def __init__(self):
        super().__init__('voice_controller')
        self.subscription = self.create_subscription(
            Voice,
            '/voice/text',
            self.listener_callback,
            10)

    def listener_callback(self, msg):
        self.get_logger().info(f'Heard Command: {msg.text} from angle {msg.direction}')

def main(args=None):
    rclpy.init(args=args)
    node = VoiceController()
    rclpy.spin(node)
    rclpy.shutdown()
