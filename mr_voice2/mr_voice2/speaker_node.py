import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import pyttsx3
from rclpy.parameter import Parameter

class SpeakerNode(Node):
    def __init__(self):
        super().__init__('speaker_node')
        
        # Declare parameters
        self.declare_parameter('rate', 170)
        self.declare_parameter('volume', 1.0)
        self.declare_parameter('lang', 'en-US')
        self.declare_parameter('is_saying', False)

        rate = self.get_parameter('rate').value
        volume = self.get_parameter('volume').value
        lang = self.get_parameter('lang').value

        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", rate)
        self.engine.setProperty("volume", volume)
        self.engine.setProperty("voice", lang)

        self.subscription = self.create_subscription(String, '~/say', self.callback_say, 10)
        self.get_logger().info("Speaker Node OK.")

    def callback_say(self, msg):
        # Set parameter to True using the correct plural method
        self.set_parameters([rclpy.parameter.Parameter('is_saying', rclpy.Parameter.Type.BOOL, True)])
        
        self.get_logger().info(f"Speaking: {msg.data}")
        
        try:
            self.engine.say(msg.data)
            self.engine.runAndWait()
        finally:
            # Ensure we set it back to False even if the engine fails
            self.set_parameters([rclpy.parameter.Parameter('is_saying', rclpy.Parameter.Type.BOOL, False)])

def main(args=None):
    rclpy.init(args=args)
    node = SpeakerNode()
    rclpy.spin(node)
    rclpy.shutdown()
