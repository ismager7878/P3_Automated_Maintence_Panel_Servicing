from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess, TimerAction, RegisterEventHandler
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import os

def generate_launch_description():
    # Launch file runs from: install/amps_python/share/amps_python/launch/
    # .venv is at workspace root, so go up 5 levels: ../../../../../.venv

    # launch_dir = os.path.dirname(os.path.realpath(__file__))
    # ws_root = os.path.abspath(os.path.join(launch_dir, "../../../../../"))
    # venv_python = os.path.join(ws_root, ".venv", "bin", "python3")

    ws_path = os.path.expanduser("~/anaconda3/envs/P3")
    venv_python = os.path.join(ws_path, "bin", "python")

    ur_driver_launch_dir = PathJoinSubstitution([FindPackageShare('ur_robot_driver'), 'launch', 'ur_control.launch.py'])
    realsense_launch_dir = PathJoinSubstitution([FindPackageShare('realsense2_camera'), 'launch', 'rs_launch.py'])
    # Start the UR driver
    ur_driver = IncludeLaunchDescription(
                            ur_driver_launch_dir,
                            launch_arguments={
                                'robot_ip': LaunchConfiguration('robot_ip'),
                                'ur_type': LaunchConfiguration('ur_type'),
                                'headless_mode': 'true',
                            }.items(),
                        )
    realsense_camera = IncludeLaunchDescription(
        realsense_launch_dir,
    )


    fp_matcher = Node(
        package='amps_cpp',
        executable='fp_matcher',
        name='fp_matcher',
    )

    Handeye = Node(
        package="amps_python",
        executable="Handeye",
        name="Handeye",
        prefix=[venv_python, " "],
    )

    return LaunchDescription([
        DeclareLaunchArgument('robot_ip', default_value='192.168.57.101'),
        DeclareLaunchArgument('ur_type', default_value='ur3e'),
        ur_driver,
        realsense_camera,
        fp_matcher,
        Handeye,
    ])

