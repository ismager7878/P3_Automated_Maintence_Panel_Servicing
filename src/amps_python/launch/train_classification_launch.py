from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os
from launch_ros.substitutions import FindPackageShare  

from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    launch_dir = os.path.dirname(os.path.realpath(__file__))
    ws_root = os.path.abspath(os.path.join(launch_dir, "../../../../../"))
    venv_python = os.path.join(ws_root, ".venv", "bin", "python3")
    
    return LaunchDescription([

        IncludeLaunchDescription(
             PathJoinSubstitution([FindPackageShare('amps_cpp'), 'launch', 'training_data.launch.py'])
        ),
       
        Node(
            package="amps_python",
            executable="knn_node",
            name="train_knn_image",
            prefix=[venv_python, " "],
            output="screen"
        ),
    ])