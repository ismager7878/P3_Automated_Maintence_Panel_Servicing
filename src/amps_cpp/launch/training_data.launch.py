from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, TimerAction, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition


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
        arguments=['--ros-args', '--log-level', 'WARN']
        
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
        output='screen',
        arguments=['--ros-args', '--log-level', 'WARN']
    )
    
    training_data_converter = Node(
        package='amps_cpp',
        executable='training_data_converter',
        name='training_data_converter',
        output='screen',
        arguments=['--ros-args', '--log-level', 'WARN']
    )

    set_state = ExecuteProcess(
        cmd=['ros2', 'topic', 'pub', '--once', '/amps/set_program_state', 'amps_cpp/msg/ProgramState', '{state: 7, state_str: "inital_state"}'],
        output='screen',
        condition=IfCondition(LaunchConfiguration('test_data', default='true'))
    )

    delayed_start = TimerAction(
        period=1.0,  # Wait 5 seconds before starting segmentation nodes
        actions=[
            set_state
        ]
    )

    return LaunchDescription([
        preprocessing,
        dataset_broadcaster,
        ground_truth_broadcaster,
        state_broadcaster_node,
        training_data_converter,
        delayed_start
    ])
    
    