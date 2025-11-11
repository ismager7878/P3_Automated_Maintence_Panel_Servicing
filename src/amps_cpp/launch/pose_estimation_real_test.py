from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess, TimerAction, RegisterEventHandler
from launch.event_handlers import OnProcessStart
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
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

    ur_wrapper = Node(
        package='amps_cpp',
        executable='ur_wrapper_node',
        name='ur_wrapper_node',
        output='screen'
    )

    pose_estimator = Node(
        package='amps_cpp',
        executable='pose_estimation',
        name='pose_estimation',
        output='screen'
    )

    delayed_nodes_start = TimerAction(
        period=16.0,  # Start nodes after controller state change
        actions=[
            fp_matcher,
            ur_wrapper,
            pose_estimator
        ]
    )

    return LaunchDescription([
        DeclareLaunchArgument('robot_ip', default_value='192.168.57.101'),
        DeclareLaunchArgument('ur_type', default_value='ur3e'),
        ur_driver,
        realsense_camera,
        delayed_nodes_start,
    ])
