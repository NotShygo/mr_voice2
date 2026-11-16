import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import pyaudio
import numpy as np
import wave
import os
import time

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

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000 ,
            input=True,
            frames_per_buffer=1024,
            stream_callback=self.stream_callback
        )
        self.get_logger().info(f"Mic Node OK. Sensitivity: {self.threshold}")

    def stream_callback(self, in_data, frame_count, time_info, status):
        # Convert buffer to numpy array to calculate volume
        data = np.frombuffer(in_data, dtype=np.int16)
        rms = np.sqrt(np.mean(data.astype(float)**2))

        if rms > self.threshold:
            # Sound detected
            if not self.recording:
                self.get_logger().info("Recording started...")
                self.recording = True
            
            self.audio_buffer.append(in_data)
            self.silence_start = None # Reset silence timer
        else:
            # Silence detected
            if self.recording:
                if self.silence_start is None:
                    self.silence_start = time.time()
                
                # Check if silence has lasted long enough to stop
                if (time.time() - self.silence_start) > self.silence_limit:
                    self.save_audio()
                else:
                    # Still within silence limit, keep buffering silence
                    self.audio_buffer.append(in_data)

        return (in_data, pyaudio.paContinue)

    def save_audio(self):
        self.recording = False
        self.silence_start = None
        
        # Generate unique filename
        filename = f"mic-{int(time.time())}.wav"
        filepath = os.path.join(self.audio_dir, filename)

        # Write to WAV file
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(b''.join(self.audio_buffer))

        self.get_logger().info(f"Saved: {filepath}")
        
        # Publish path for STT node
        msg = String()
        msg.data = filepath
        self.pub.publish(msg)

        # Clear buffer
        self.audio_buffer = []

def main(args=None):
    rclpy.init(args=args)
    node = MicNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stream.stop_stream()
        node.stream.close()
        node.p.terminate()
        node.destroy_node()
        rclpy.shutdown()
