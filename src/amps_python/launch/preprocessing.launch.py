from launch import LaunchDescription
from launch_ros.actions import Node
import os
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
    
def generate_launch_description():
    # Launch file runs from: install/amps_python/share/amps_python/launch/
    # .venv is at workspace root, so go up 5 levels: ../../../../../.venv


    # launch_dir = os.path.dirname(os.path.realpath(__file__))
    # ws_root = os.path.abspath(os.path.join(launch_dir, "../../../../../"))
    # venv_python = os.path.join(ws_root, ".venv", "bin", "python3")

    ws_path = os.path.expanduser("~/anaconda3/envs/P3")
    venv_python = os.path.join(ws_path, "bin", "python")



    return LaunchDescription([

        DeclareLaunchArgument(
            'debugging',
            default_value='true',
            description='Whether to run preprocessing in debugging mode.'
        ),
        
        Node(
            package="amps_python",
            executable="preprocessing_node",
            name="preprocessing_node",
            output="screen",
            prefix=[venv_python, " "],  # Run using venv Python
            parameters=[{
                'debugging': LaunchConfiguration('debugging')
            }]
        ),
    ])