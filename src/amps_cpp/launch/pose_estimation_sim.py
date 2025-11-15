from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess, TimerAction, RegisterEventHandler
from launch.event_handlers import OnProcessStart
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    ur_driver_launch_dir = PathJoinSubstitution([FindPackageShare('ur_robot_driver'), 'launch', 'ur_control.launch.py'])

    # Start the UR driver
    ur_driver = IncludeLaunchDescription(
                            ur_driver_launch_dir,
                            launch_arguments={
                                'robot_ip': LaunchConfiguration('robot_ip'),
                                'ur_type': LaunchConfiguration('ur_type'),
                                'headless_mode': 'true',
                            }.items(),
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

    frame_broadcaster = Node(
        package='amps_cpp',
        executable='frame_broadcaster',
        name='frame_broadcaster',
    )

    # Wait for driver to be ready, then set tcp_pose_broadcaster state
    delayed_controller_disable = TimerAction(
        period=10.0,  # Wait 15 seconds after launch for driver to be ready
        actions=[
            ExecuteProcess(
                cmd=['ros2', 'control', 'set_controller_state', 'tcp_pose_broadcaster', LaunchConfiguration('tcp_broadcaster_state')],
                output='screen'
            ),
        ]
    )

    delayed_nodes_start = TimerAction(
        period=18.0,  # Start nodes after controller state change
        actions=[
            fp_matcher,
            ur_wrapper,
            pose_estimator,
            frame_broadcaster
        ]
    )

    staticCamFrameBroadcaster = Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=[
                '--x', '0.02', '--y', '-0.057', '--z', '0.02',
                '--yaw', '0', '--pitch', '0', '--roll',
                '0', '--frame-id', 'tool0', '--child-frame-id', 'camera']
    )


    return LaunchDescription([
        DeclareLaunchArgument('robot_ip', default_value='192.168.56.101'),
        DeclareLaunchArgument('ur_type', default_value='ur3e'),
        DeclareLaunchArgument('tcp_broadcaster_state', default_value='inactive'),
        ur_driver,
        staticCamFrameBroadcaster,
        delayed_controller_disable,
        delayed_nodes_start,
    ])
