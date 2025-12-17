from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess, TimerAction, RegisterEventHandler
from launch.event_handlers import OnProcessStart
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
import yaml
import os

from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    launch_dir = os.path.dirname(os.path.realpath(__file__))
    ws_root = os.path.abspath(os.path.join(launch_dir, "../../../../../"))
    venv_python = os.path.join(ws_root, ".venv", "bin", "python3")


    pose_estimator = IncludeLaunchDescription(
        PathJoinSubstitution([FindPackageShare('amps_cpp'), 'launch', 'pose_estimation_real_test.py']),
    )

    preprocessing = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('amps_python'), 'launch', 'preprocessing.launch.py')]),
        launch_arguments={
            'debugging': 'false',
            'real_data': 'true'
            }.items()
            
    )

    segmentation_node = Node(
        package='amps_cpp',
        executable='segmentation',
        name='segmentation_node',
        output='screen',
        arguments=['--ros-args', '--log-level', 'WARN']
    )

    classification_node = Node(
            package="amps_python",
            executable="classified_image",
            name="classified_image",
            output="screen",
            arguments=['--ros-args', '--log-level', 'WARN'],
            prefix=[venv_python, " "],
    )

    button_state_detector = Node(
        package='amps_cpp',
        executable='button_state_detector',
        name='button_state_detector',
        output='screen',
        arguments=['--ros-args', '--log-level', 'WARN'],
        remappings=[('/amps/training_data', '/amps/vision/type_classification')],
    )

    state_set = ExecuteProcess(
        cmd=['ros2', 'topic', 'pub', '--once', '/amps/set_program_state', 'amps_cpp/msg/ProgramState', '{state: 1, state_str: "inital_state"}'],
        output='screen',
    )


    return LaunchDescription([
        preprocessing,
        pose_estimator,
        segmentation_node,
        classification_node,
        button_state_detector,
        TimerAction(
            period=12.0,
            actions=[
                state_set
            ]
        ),
    ])

    




