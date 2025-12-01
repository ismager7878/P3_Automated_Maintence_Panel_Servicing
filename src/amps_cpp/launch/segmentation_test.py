from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    segmentation_sub_node = Node(
        package='amps_cpp',
        executable='subscribe_segmentation',
        name='segmentation_subscriber',
        output='screen'
    )

    segmentation_pub_node = Node(
        package='amps_cpp',
        executable='publish_segmentation',
        name='segmentation_publisher',
        output='screen'
    )

    segmentation_node = Node(
        package='amps_cpp',
        executable='segmentation',
        name='segmentation_node',
        output='screen'
    )

  
    return LaunchDescription([
        segmentation_sub_node,
        segmentation_pub_node,
        segmentation_node,
    ])
