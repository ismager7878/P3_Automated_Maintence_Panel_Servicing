from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os
from launch_ros.substitutions import FindPackageShare  
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # Launch file runs from: install/amps_python/share/amps_python/launch/
    # .venv is at workspace root, so go up 5 levels: ../../../../../.venv
    launch_dir = os.path.dirname(os.path.realpath(__file__))
    ws_root = os.path.abspath(os.path.join(launch_dir, "../../../../../"))
    venv_python = os.path.join(ws_root, ".venv", "bin", "python3")

    fox_glove_launch_dir = PathJoinSubstitution([FindPackageShare('foxglove_bridge'), 'launch', 'foxglove_bridge_launch.xml'])

    foxglove_bridge = IncludeLaunchDescription(
        fox_glove_launch_dir,
    )
    return LaunchDescription([
        foxglove_bridge,

        DeclareLaunchArgument(
            'training_data',
            default_value='false'
        ),

        DeclareLaunchArgument(
            'impl_test',
            default_value='true'
        ),

        IncludeLaunchDescription(
                PathJoinSubstitution([FindPackageShare('amps_cpp'), 'launch', 'button_state.launch.py']),
                launch_arguments={'use_classification': LaunchConfiguration('impl_test')}.items(),
        ),
       
       #vi skal måske lave en separat launch fil:
        Node(
            package="amps_python",
            executable="state_test",
            name="state_test",
            output="screen",
            prefix=[venv_python, " "],
        )

        
    ])