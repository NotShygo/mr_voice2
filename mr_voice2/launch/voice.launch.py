import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.conditions import IfCondition, UnlessCondition

def generate_launch_description():
    use_respeaker_arg = DeclareLaunchArgument(
        'use_respeaker',
        default_value='false',
        description='Whether to use the Respeaker hardware or standard MicNode'
    )

    speaker_node = Node(
        package='mr_voice2',
        executable='speaker',
        name='speaker',
        output='screen',
        parameters=[{'rate': 170, 'volume': 1.0, 'lang': 'en-US'}],
        emulate_tty=True
    )

    stt_node = Node(
        package='mr_voice2',
        executable='stt',
        name='voice',
        output='screen',
        parameters=[{
            'topic_audio_path': '/voice/audio_path', # Adjusted to match mic_node/respeaker output
            'lang': 'en-US'
        }],
        emulate_tty=True
    )

    respeaker_node = Node(
        package='mr_voice2',
        executable='respeaker',
        name='respeaker',
        output='screen',
        parameters=[{'buffer_size': 10, 'audio_directory': '/tmp/speech/'}],
        condition=IfCondition(LaunchConfiguration('use_respeaker')),
        # Remap output to match what STT node expects
        remappings=[('~/audio_path', '/voice/audio_path')],
        emulate_tty=True
    )

    # Added MicNode for when use_respeaker is false
    mic_node = Node(
        package='mr_voice2',
        executable='mic_node',
        name='mic_node',
        output='screen',
        parameters=[{'audio_directory': '/tmp/speech/'}],
        condition=UnlessCondition(LaunchConfiguration('use_respeaker')),
        # Remap output to match what STT node expects
        remappings=[('~/audio_path', '/voice/audio_path')],
        emulate_tty=True
    )

    return LaunchDescription([
        use_respeaker_arg,
        speaker_node,
        stt_node,
        respeaker_node,
        mic_node
    ])