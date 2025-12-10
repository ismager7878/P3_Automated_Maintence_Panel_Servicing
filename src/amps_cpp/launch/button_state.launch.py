from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, TimerAction, ExecuteProcess, DeclareLaunchArgument
from launch import LaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
import os
from ament_index_python.packages import get_package_share_directory

from launch.conditions import IfCondition, UnlessCondition



def generate_launch_description():
    test_data_arg = DeclareLaunchArgument(
        'test_data',
        default_value='true'
    )

    training_data_converter = IncludeLaunchDescription(
        PathJoinSubstitution([FindPackageShare('amps_cpp'), 'launch', 'training_data.launch.py']),
        condition=UnlessCondition(LaunchConfiguration('use_classification')),
        launch_arguments={'test_data': LaunchConfiguration('test_data')}.items()
    )


    classificationNode = IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('amps_python'), 'launch', 'classification_launch.py')]),
            condition=IfCondition(LaunchConfiguration('use_classification'))
    )

    button_state_detector_test = Node(
        package='amps_cpp',
        executable='button_state_detector',
        name='button_state_detector',
        output='screen',
        condition=UnlessCondition(LaunchConfiguration('use_classification'))
    )  

    button_state_detector = Node(
        package='amps_cpp',
        executable='button_state_detector',
        name='button_state_detector',
        output='screen',
        remappings=[('/amps/training_data', 'object_classification_topic')],
        condition=IfCondition(LaunchConfiguration('use_classification'))
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_classification',
            default_value='true',
            description='Whether to use test data or use live data from the robot.'
        ),
        test_data_arg,
        training_data_converter,
        button_state_detector,
        classificationNode,
        button_state_detector_test,
    ])