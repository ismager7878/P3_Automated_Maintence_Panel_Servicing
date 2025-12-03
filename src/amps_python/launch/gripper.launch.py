from launch import LaunchDescription
from launch_ros.actions import Node
import os

def generate_launch_description():
    # Launch file runs from: install/amps_python/share/amps_python/launch/
    # .venv is at workspace root, so go up 5 levels: ../../../../../.venv
    launch_dir = os.path.dirname(os.path.realpath(__file__))
    ws_root = os.path.abspath(os.path.join(launch_dir, "../../../../../"))
    venv_python = os.path.join(ws_root, ".venv", "bin", "python3")

    return LaunchDescription([
        Node(
            package="amps_python",
            executable="gripper_node",
            name="gripper_node",
            output="screen",
            prefix=[venv_python, " "],
        ),
    ])