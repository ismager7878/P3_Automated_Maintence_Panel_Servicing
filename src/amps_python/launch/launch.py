from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
import os


def generate_launch_description():
    pkg_share = FindPackageShare('realsense2_camera').find('realsense2_camera')
    launch_file_path = os.path.join(pkg_share, 'launch', 'rs_launch.py')

    return LaunchDescription([
        # Launch the RealSense camera with specific depth and color profiles
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(launch_file_path),
            launch_arguments={
                'depth_module.depth_profile': '1280x720x30',
                'color_module.color_profile': '1920x1080x30'
            }.items()
        ),
        
        # Launch the ur robot driver with a specified robot IP address
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                FindPackageShare('ur_robot_driver').find('ur_robot_driver'), 'launch', 'ur_control.launch.py')),
            launch_arguments={
                'robot_ip': '192.168.57.101',
                'ur_type': 'ur3e'
                #'headless_mode': 'true' # Uncomment this line to run in headless mode when we want to control robot
            }.items()
        )
        
        # # Launch Foxglove Bridge so the camera topics are available to Foxglove Studio
        # IncludeLaunchDescription(
        #     PythonLaunchDescriptionSource(os.path.join(
        #         FindPackageShare('foxglove_bridge').find('foxglove_bridge'), 'launch', 'foxglove_bridge_launch.py')),
        #     launch_arguments={'transport_type': 'websocket'}.items()
        # )
    ])
