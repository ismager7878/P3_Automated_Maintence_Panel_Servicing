from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, TimerAction, ExecuteProcess
from launch import LaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    preprocessing = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('amps_python'), 'launch', 'preprocessing.launch.py')]),
    )

    dataset_broadcaster = Node(
        package='amps_cpp',
        executable='dataset_broadcaster',
        name='dataset_broadcaster',
        output='screen',
        
    )

    button_state_detector = Node(
        package='amps_cpp',
        executable='button_state_detector',
        name='button_state_detector',
        output='screen',
    )   

    return LaunchDescription([
        preprocessing,
        TimerAction(
            period=3.0,  # Wait for preprocessing to finish
            actions=[
                dataset_broadcaster,
                button_state_detector,
            ]
        ),
    ])