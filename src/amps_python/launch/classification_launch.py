from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os
from launch_ros.substitutions import FindPackageShare  

from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    return LaunchDescription([

        IncludeLaunchDescription(
             PathJoinSubstitution([FindPackageShare('amps_cpp'), 'launch', 'segmentation_test.py'])
        ),
       
        Node(
            package="amps_python",
            executable="classified_image",
            name="classified_image",
            output="screen"
        ),
    ])