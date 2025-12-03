from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction, ExecuteProcess, DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition

import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    launchDesc = LaunchDescription()

    test_data_arg = DeclareLaunchArgument(
        'test_data',
        default_value='true',
        description='Whether to use test data or use live data from the robot.'
    )

    launchDesc.add_action(test_data_arg)

    preprocessing = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('amps_python'), 'launch', 'preprocessing.launch.py')]),
    )

    segmentation_node = Node(
        package='amps_cpp',
        executable='segmentation',
        name='segmentation_node',
        output='screen'
    )

    ground_truth_broadcaster = Node(
        package='amps_cpp',
        executable='ground_truth_broadcaster',
        name='ground_truth_broadcaster',
        output='screen',
        condition=IfCondition(LaunchConfiguration('test_data', default='true')),
        arguments=['--ros-args', '--log-level', 'WARN']
    )

    dataset_broadcaster = Node(
        package='amps_cpp',
        executable='dataset_broadcaster',
        name='dataset_broadcaster',
        output='screen',
        condition=IfCondition(LaunchConfiguration('test_data', default='true')),
        arguments=['--ros-args', '--log-level', 'WARN']
    )

    state_broadcaster_node = Node(
        package='amps_cpp',
        executable='state_broadcaster',
        name='state_broadcaster_node',
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

    launchDesc.add_action(preprocessing)
    launchDesc.add_action(segmentation_node)
    launchDesc.add_action(state_broadcaster_node)
    launchDesc.add_action(ground_truth_broadcaster)
    launchDesc.add_action(dataset_broadcaster)
    launchDesc.add_action(delayed_start)

    return launchDesc
    
