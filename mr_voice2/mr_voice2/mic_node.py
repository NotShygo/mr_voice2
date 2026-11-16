import os
import time
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import sounddevice as sd
import wave

class MicNode(Node):
    def __init__(self):
        super().__init__('mic_node')
        self.declare_parameter('audio_directory', '/tmp/speech')
        self.declare_parameter('threshold', 5000)  # Sensitivity (lower = more sensitive)
        self.declare_parameter('silence_limit', 1.5) # Seconds of silence before saving
        
        self.audio_dir = self.get_parameter('audio_directory').value
        self.threshold = self.get_parameter('threshold').value
        self.silence_limit = self.get_parameter('silence_limit').value
        
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)

        self.pub = self.create_publisher(String, '~/audio_path', 10)
        
        # Internal State
        self.audio_buffer = []
        self.recording = False
        self.silence_start = None

        self.stream = sd.InputStream(
            samplerate=16000,
            channels=1,
            dtype='int16',
            blocksize=1024,
            callback=self.stream_callback
        )
        self.stream.start()
        self.get_logger().info(f"Mic Node OK. Sensitivity: {self.threshold}")

    def stream_callback(self, indata, frames, time_info, status):
        if status:
            self.get_logger().warn(str(status))

        data = indata.flatten()
        rms = np.sqrt(np.mean(data.astype(float)**2))

        if rms > self.threshold:
            if not self.recording:
                self.get_logger().info("Recording started...")
                self.recording = True
            
            self.audio_buffer.append(data.copy())
            self.silence_start = None
        else:
            if self.recording:
                if self.silence_start is None:
                    self.silence_start = time.time()
                
                if (time.time() - self.silence_start) > self.silence_limit:
                    self.save_audio()
                else:
                    self.audio_buffer.append(data.copy())

    def save_audio(self):
        self.recording = False
        self.silence_start = None
        
        filename = f"mic-{int(time.time())}.wav"
        filepath = os.path.join(self.audio_dir, filename)

        audio_data = np.concatenate(self.audio_buffer)

        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # int16 = 2 bytes
            wf.setframerate(16000)
            wf.writeframes(audio_data.tobytes())

        self.get_logger().info(f"Saved: {filepath}")
        
        msg = String()
        msg.data = filepath
        self.pub.publish(msg)

        self.audio_buffer = []

def main(args=None):
    rclpy.init(args=args)
    node = MicNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stream.stop()
        node.stream.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
