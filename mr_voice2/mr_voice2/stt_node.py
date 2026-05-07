import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import speech_recognition as sr
from threading import Thread
from mr_voice_interfaces.msg import Voice

class SpeechToTextNode(Node):
    def __init__(self):
        super().__init__('stt_node')
        
        # Parameters
        self.declare_parameter('topic_audio_path', '/respeaker/audio_path')
        self.declare_parameter('lang', 'en-US')
        
        self.lang = self.get_parameter('lang').value
        self.sr = sr.Recognizer()

        # Pub/Sub
        self.subscription = self.create_subscription(
            String, 
            self.get_parameter('topic_audio_path').value, 
            self.callback_audio_path, 
            10)
        self.pub_voice = self.create_publisher(Voice, '~/text', 10)
        
        self.get_logger().info("STT Node OK.")

    def callback_audio_path(self, msg):
        # Run recognition in a thread to avoid blocking the ROS executor
        Thread(target=self._recognize_thread, args=(msg.data,)).start()

    def _recognize_thread(self, path):
            direction = 0
            try:
                # Logic: extract direction from "filename-direction.wav" 
                # Note: Your mic_node saves as "mic-timestamp.wav", so this may default to 0
                parts = path.split("/")[-1].split(".")[0].split("-")
                if len(parts) > 1:
                    direction = int(parts[1])
            except Exception:
                direction = 0

            with sr.AudioFile(path) as source:
                audio = self.sr.record(source)
                
            try:
                self.get_logger().info(f"Recognizing: {path}")
                text = self.sr.recognize_google(audio, language=self.lang)
                
                if text:
                    # Create the message
                    msg = Voice()
                    
                    # 1. Populate Header and Time
                    now = self.get_clock().now().to_msg()
                    msg.header.stamp = now
                    msg.header.frame_id = "map"
                    msg.time = now # builtin_interfaces/Time
                    
                    # 2. Populate Strings
                    msg.text = text
                    import datetime
                    msg.timestring = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # 3. Populate Direction (uint16)
                    # Using the direction parsed from filename, or 0
                    msg.direction = max(0, min(int(direction), 65535))

                    # FIX: Use the correct variable name defined in __init__
                    self.pub_voice.publish(msg)
                    self.get_logger().info(f"Published: '{text}'")
                    
            except sr.UnknownValueError:
                self.get_logger().warn("Google STT could not understand audio")
            except Exception as e:
                self.get_logger().error(f"STT Error: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = SpeechToTextNode()
    rclpy.spin(node)
    rclpy.shutdown()
