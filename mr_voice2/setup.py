from setuptools import setup
import os
from glob import glob

package_name = 'mr_voice2'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # This line is CRITICAL:
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pcms',
    entry_points={
        'console_scripts': [
            'speaker = mr_voice2.speaker_node:main',
            'stt = mr_voice2.stt_node:main',
            'respeaker = mr_voice2.respeaker_node:main',
            'mic_node = mr_voice2.mic_node:main',
        ],
    },
)
