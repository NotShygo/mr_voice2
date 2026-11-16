import os
import struct
import time
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import sounddevice as sd
import usb.core
import usb.util
import wave
from pixel_ring import usb_pixel_ring_v2

class RespeakerNode(Node):
    def __init__(self):
        super().__init__('respeaker_node')
        self.declare_parameter('buffer_size', 10)
        self.declare_parameter('audio_directory', '/tmp/speech')

        self.max_buf = self.get_parameter('buffer_size').value
        self.audio_dir = self.get_parameter('audio_directory').value
        
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)

        self.pub = self.create_publisher(String, '~/audio_path', 10)
        
        # Initialize Hardware
        self.dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)
        if not self.dev:
            self.get_logger().error("ReSpeaker device not found!")
            return
            
        self.dev.reset()
        self.pixel_ring = usb_pixel_ring_v2.PixelRing(self.dev)
        self.pixel_ring.think()
        
        # Audio setup
        self.audio_buf = []
        self.is_voice_buf = []
        self.direction_buf = []
        
        self.stream = sd.InputStream(
            samplerate=16000,
            channels=6,
            dtype='int16',
            blocksize=1024,
            callback=self.stream_callback
        )
        self.stream.start()
        self.get_logger().info("Respeaker Node Started")

    def stream_callback(self, indata, frames, time_info, status):
        if status:
            self.get_logger().warn(str(status))

        # indata shape is (frames, channels), dtype is int16
        # Channel 0 is processed audio
        if len(self.is_voice_buf) >= self.max_buf:
            self.is_voice_buf.pop(0)
        
        is_v = self.read_vad() 
        self.is_voice_buf.append(is_v)

        if sum(self.is_voice_buf) == 0 and len(self.audio_buf) > 0:
            self.save_and_publish()
        elif is_v:
            self.audio_buf.append(indata.copy())

    def read_vad(self):
        # Implementation of your USB control transfer to read 'VOICEACTIVITY'
        return 1  # Simplified

    def save_and_publish(self):
        filename = f"respeaker-{int(time.time())}.wav"
        filepath = os.path.join(self.audio_dir, filename)

        audio_data = np.concatenate(self.audio_buf, axis=0)

        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(6)
            wf.setsampwidth(2)  # int16 = 2 bytes
            wf.setframerate(16000)
            wf.writeframes(audio_data.tobytes())

        self.get_logger().info(f"Saved: {filepath}")
        
        msg = String()
        msg.data = filepath
        self.pub.publish(msg)

        self.audio_buf = []

def main(args=None):
    rclpy.init(args=args)
    node = RespeakerNode()
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
