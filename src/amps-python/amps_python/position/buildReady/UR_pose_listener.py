import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import PoseStamped

import numpy as np
import spatialmath as spm


class ImagePoseListener(Node):
    def __init__(self):
        super().__init__('image_pose_listener')

        # QoS for sensordata (kamera/pose fra bag): ofte BEST_EFFORT og lille depth
        sensor_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST
        )

        self.sub_pose = self.create_subscription(
            PoseStamped,
            '/tcp_pose_broadcaster/pose',
            self.quaternion2rotationMatrix,
            sensor_qos
        )

    def quaternion2rotationMatrix(self, msg):
        ori = msg.pose.orientation
        p = msg.pose.position
        q = spm.UnitQuaternion([ori.w, ori.x, ori.y, ori.z])
        R = q.R

        np.set_printoptions(precision=4, suppress=True)  # Set print options for better readability

        r_mat = spm.SO3(R)

        print(f"Rotation matrix:")
        print(r_mat)
        #print("position vector:")
        #print(p)



def main():
    rclpy.init()
    node = ImagePoseListener()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
