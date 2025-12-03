from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, TimerAction, ExecuteProcess
from launch import LaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    training_data_converter = IncludeLaunchDescription(
        PathJoinSubstitution([FindPackageShare('amps_cpp'), 'launch', 'training_data.launch.py']),
    )

    button_state_detector = Node(
        package='amps_cpp',
        executable='button_state_detector',
        name='button_state_detector',
        output='screen',
    )   

    return LaunchDescription([
        training_data_converter,
        button_state_detector,
    ])