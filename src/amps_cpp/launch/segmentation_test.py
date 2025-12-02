from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction, ExecuteProcess


def generate_launch_description():
    segmentation_sub_node = Node(
        package='amps_cpp',
        executable='subscribe_segmentation',
        name='segmentation_subscriber',
        output='screen'
    )

    segmentation_pub_node = Node(
        package='amps_cpp',
        executable='publisher_segmentation',
        name='segmentation_publisher',
        output='screen'
    )

    segmentation_node = Node(
        package='amps_cpp',
        executable='segmentation',
        name='segmentation_node',
        output='screen'
    )

    state_broadcaster_node = Node(
        package='amps_cpp',
        executable='state_broadcaster',
        name='state_broadcaster_node',
        output='screen'
    )

    set_state = ExecuteProcess(
                cmd=['ros2', 'topic', 'pub', '--once', '/amps/set_program_state', 'amps_cpp/msg/ProgramState', '{state: 7, state_str: "inital_state"}'],
                output='screen'
            )

    delayed_start = TimerAction(
        period=1.0,  # Wait 5 seconds before starting segmentation nodes
        actions=[
            set_state
        ]
    )
  
    return LaunchDescription([
        segmentation_node,
        segmentation_sub_node,
        segmentation_pub_node,
        state_broadcaster_node,
        delayed_start
    ])
    