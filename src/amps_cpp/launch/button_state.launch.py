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

    ground_truth_broadcaster = Node(
        package='amps_cpp',
        executable='ground_truth_broadcaster',
        name='ground_truth_broadcaster',
        output='screen',
        arguments=['--ros-args', '--log-level', 'WARN']
    )

    state_broadcaster_node = Node(
        package='amps_cpp',
        executable='state_broadcaster',
        name='state_broadcaster_node',
        output='screen'
    )

    button_state_detector = Node(
        package='amps_cpp',
        executable='button_state_detector',
        name='button_state_detector',
        output='screen',
    )   

    set_state = ExecuteProcess(
        cmd=['ros2', 'topic', 'pub', '--once', '/amps/set_program_state', 'amps_cpp/msg/ProgramState', '{state: 7, state_str: "inital_state"}'],
        output='screen',
    )

    return LaunchDescription([
        preprocessing,
        dataset_broadcaster,
        button_state_detector,
        ground_truth_broadcaster,
        state_broadcaster_node,
        TimerAction(
            period=2.0,  # Wait for other nodes to initialize
            actions=[set_state]
        )
    ])