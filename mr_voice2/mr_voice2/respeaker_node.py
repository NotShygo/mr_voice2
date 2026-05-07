import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import usb.core
import usb.util
import struct
import time
import pyaudio
import numpy as np
import wave
import os
from pixel_ring import usb_pixel_ring_v2

# ... (Keep the PARAMETERS dictionary from your original script) ...

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
        self.p = pyaudio.PyAudio()
        self.audio_buf = []
        self.is_voice_buf = []
        self.direction_buf = []
        
        self.stream = self.p.open(
            input=True,
            format=pyaudio.paInt16,
            channels=6,
            rate=16000,
            frames_per_buffer=1024,
            stream_callback=self.stream_callback
        )
        self.get_logger().info("Respeaker Node Started")

    def stream_callback(self, in_data, frame_count, time_info, status):
        data = np.frombuffer(in_data, dtype=np.int16)
        # Channel 0 is processed audio
        if len(self.is_voice_buf) >= self.max_buf: self.is_voice_buf.pop(0)
        
        # In ROS 2, checking parameters of other nodes (like 'is_saying') 
        # is done via a ParameterClient, but here we keep it simple.
        is_v = self.read_vad() 
        self.is_voice_buf.append(is_v)

        if sum(self.is_voice_buf) == 0 and len(self.audio_buf) > 0:
            self.save_and_publish()
        elif is_v:
            self.audio_buf.append(in_data)
            
        return None, pyaudio.paContinue

    def read_vad(self):
        # Implementation of your USB control transfer to read 'VOICEACTIVITY'
        return 1 # Simplified for space

    def save_and_publish(self):
        # logic to write wave file and pub.publish(path)
        pass

def main(args=None):
    rclpy.init(args=args)
    node = RespeakerNode()
    rclpy.spin(node)
    rclpy.shutdown()
