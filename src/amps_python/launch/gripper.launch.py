from launch import LaunchDescription
from launch_ros.actions import Node
import os
import sys


def _resolve_venv_python():
    """
    Resolve the interpreter to use for the node.
    Assumes the user runs from the workspace root and venv is at `.venv`.
    Fallback to current interpreter if `.venv` isn't present.
    """
    cwd = os.getcwd()
    candidate = os.path.join(cwd, ".venv", "bin", "python3")
    if os.path.exists(candidate):
        return candidate

    # Fallback: try workspace root inferred from this file location (installed share path)
    try:
        launch_dir = os.path.dirname(os.path.realpath(__file__))
        # When installed, this file lives under `<prefix>/share/amps_python/launch/`
        # The workspace root (where `.venv` would be) is typically the CWD when launching.
        # Still, attempt an additional heuristic going up a few levels.
        ws_root_guess = os.path.abspath(os.path.join(launch_dir, "../../../../"))
        candidate2 = os.path.join(ws_root_guess, ".venv", "bin", "python3")
        if os.path.exists(candidate2):
            return candidate2
    except Exception:
        pass

    # Last resort: use the current interpreter
    return sys.executable


def generate_launch_description():
    venv_python = _resolve_venv_python()

    return LaunchDescription([
        Node(
            package="amps_python",
            executable="gripper_node",
            name="gripper_node",
            output="screen",
            prefix=[venv_python, " "],
        ),
    ])