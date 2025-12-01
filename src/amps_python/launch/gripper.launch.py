from launch import LaunchDescription
from launch_ros.actions import Node
import os
    
def generate_launch_description():
    ws_path = os.path.expanduser("~/Documents/git_repos/P3_Automated_Maintence_Panel_Servicing")
    venv_python = os.path.join(ws_path, ".venv", "bin", "python3")
    
    # # Automatically find the workspace root relative to this launch file to locate the .venv
    # launch_dir = os.path.dirname(os.path.realpath(__file__))
    # ws_root = os.path.abspath(os.path.join(launch_dir, "../../../"))  # go up from src/my_pkg/launch/
    # venv_python = os.path.join(ws_root, ".venv", "bin", "python3")

    return LaunchDescription([
        Node(
            package="amps_python",
            executable="gripper_node",
            name="gripper_node",
            output="screen",
            prefix=[venv_python, " "],  # Run using venv Python
        ),
    ])