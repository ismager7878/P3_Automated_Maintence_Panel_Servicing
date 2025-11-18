from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess, TimerAction, RegisterEventHandler
from launch.event_handlers import OnProcessStart
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
import yaml
import os

try:
    pkg_share = get_package_share_directory('amps_python')
    yaml_path = os.path.join(pkg_share, 'data', 'handeye.yaml')
    
    with open(yaml_path, 'r') as f:
        params = yaml.safe_load(f)

    tf_params = params['/**']['ros__parameters']['camera_to_gripper']

    xyz = tf_params['translation']
    rpy = tf_params['rotation']

except Exception as e:
    # Fallback hvis noget går galt — så får du en default transform i stedet for crash
    print(f"[WARN] Could not load handeye.yaml")
    xyz = [-0.034, -0.059, 0.023]
    rpy = [0.0, 0.0, 0.0]
    tf_params = {'frame_id': 'tool0', 'child_frame_id': 'camera'}


def generate_launch_description():
    ur_driver_launch_dir = PathJoinSubstitution([FindPackageShare('ur_robot_driver'), 'launch', 'ur_control.launch.py'])
    realsense_launch_dir = PathJoinSubstitution([FindPackageShare('realsense2_camera'), 'launch', 'rs_launch.py'])
    fox_glove_launch_dir = PathJoinSubstitution([FindPackageShare('foxglove_bridge'), 'launch', 'foxglove_bridge_launch.xml'])
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
        launch_arguments={
            'enable_rgbd': 'true',
            'enable_sync': 'true',
            'align_depth.enable': 'true', 
            'enable_color': 'true',
            'enable_depth': 'true'
        }.items(),
    )

    foxglove_bridge = IncludeLaunchDescription(
        fox_glove_launch_dir,
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

    delayed_nodes_start = TimerAction(
        period=16.0,  # Start nodes after controller state change
        actions=[
            fp_matcher,
            ur_wrapper,
            pose_estimator,
            frame_broadcaster,
        ]
    )
    staticCamFrameBroadcaster = Node(
    package='tf2_ros',
    executable='static_transform_publisher',
    arguments=[
    '--x', str(xyz[0]),
    '--y', str(xyz[1]),
    '--z', str(xyz[2]),
    '--roll', str(rpy[0]),
    '--pitch', str(rpy[1]),
    '--yaw', str(rpy[2]),
    '--frame-id', tf_params['frame_id'],
    '--child-frame-id', tf_params['child_frame_id']
    ])

    return LaunchDescription([
        DeclareLaunchArgument('robot_ip', default_value='192.168.57.101'),
        DeclareLaunchArgument('ur_type', default_value='ur3e'),
        ur_driver,
        staticCamFrameBroadcaster,
        realsense_camera,
        foxglove_bridge,
        delayed_nodes_start,
    ])
