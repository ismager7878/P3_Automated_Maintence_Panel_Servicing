from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([

        Node(
            package="amps_cpp",
            executable="publisher_segmentation",
            name="publisher_segmentation",
            output="screen"
        ),

        Node(
            package="amps_cpp",
            executable="segmentation",
            name="segmentation",
            output="screen"
        ),

        Node(
            package="amps_python",
            executable="classified_image",
            name="classified_image",
            output="screen"
        ),
    ])