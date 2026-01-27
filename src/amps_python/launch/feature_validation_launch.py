from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os
from launch_ros.substitutions import FindPackageShare  
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # Launch file runs from: install/amps_python/share/amps_python/launch/
    # .venv is at workspace root, so go up 5 levels: ../../../../../.venv
    launch_dir = os.path.dirname(os.path.realpath(__file__))
    ws_root = os.path.abspath(os.path.join(launch_dir, "../../../../../"))
    venv_python = os.path.join(ws_root, ".venv", "bin", "python3")

    return LaunchDescription([

        DeclareLaunchArgument(
            'training_data',
            default_value='false'
        ),

        DeclareLaunchArgument(
            'module_test',
            default_value='false'
        ),

        IncludeLaunchDescription(
             PathJoinSubstitution([FindPackageShare('amps_cpp'), 'launch', 'segmentation_test.py']),
             launch_arguments=[
                    ('training_data', LaunchConfiguration('training_data')),
                    ('bypass_segmentation', LaunchConfiguration('module_test'))
             ]
        ),
       
       #vi skal måske lave en separat launch fil:
        Node(
        package='amps_cpp',
        executable='feature_validation',
        name='feature_validation',
        output='screen',
        ),

        Node(
            package='amps_python',
            executable='feature_validation_test',
            name='feature_validation_test',
            output='screen',
            prefix=[venv_python, " "],
        ),


        Node(
            package="amps_python",
            executable="classified_image",
            name="classified_image",
            output="screen",
            prefix=[venv_python, " "],
        ),
    ])