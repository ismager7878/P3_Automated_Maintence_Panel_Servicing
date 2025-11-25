#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from amps_python.gripper_node import MoveGripper  # replace with your package

class TestClient(Node):
    def __init__(self):
        super().__init__('gripper_test_client')
        self.cli = ActionClient(self, MoveGripper, 'gripper/move')

    def send_goal(self, pos=255, speed=255, force=255):
        self.cli.wait_for_server()
        goal_msg = MoveGripper.Goal()
        goal_msg.position = pos
        goal_msg.speed = speed
        goal_msg.force = force
        self._goal_handle = self.cli.send_goal_async(goal_msg, feedback_callback=self.feedback_cb)
        self._goal_handle.add_done_callback(self.goal_response_cb)

    def feedback_cb(self, feedback):
        fb = feedback.feedback
        print(f"FB pos={fb.current_position} force={fb.current_force} moving={fb.moving}")

    def goal_response_cb(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            print("Goal rejected")
            rclpy.shutdown()
            return
        print("Goal accepted")
        res_future = goal_handle.get_result_async()
        res_future.add_done_callback(self.result_cb)

    def result_cb(self, future):
        result = future.result().result
        print("Result:", result.success, result.message)
        rclpy.shutdown()

def main():
    rclpy.init()
    node = TestClient()
    node.send_goal(255, 255, 255)  # full close at max speed/force
    rclpy.spin(node)

if __name__ == "__main__":
    main()
