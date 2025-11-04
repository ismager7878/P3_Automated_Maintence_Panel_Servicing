import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
import numpy as np
from ament_index_python.packages import get_package_share_directory
#from geometry_msgs.msg import PoseStamped
import spatialmath as spm
from amps_cpp.msg import FrameWithPose
import math


class PoseListener(Node):
    def __init__(self):
        super().__init__('PoseListener')

        # Parametre (du kan override dem fra CLI)
        self.declare_parameter('color_topic', '/camera/camera/color/image_raw')
        sensor_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST
        )
        #--------------------------------------------------------------------------------
        #subscription 2 framwpose topic:
        # fp_matcher publishes to 'amps_cpp/pose_estimation/rgb_frame_with_pose'
        # This single subscription handles both frame and pose
        self.sub_frame_pose = self.create_subscription(
            FrameWithPose,
            'amps_cpp/pose_estimation/rgb_frame_with_pose',
            self.robotPosition,
            10)
        self.get_logger().info("Subscribed to 'amps_cpp/pose_estimation/rgb_frame_with_pose' topic. Waiting for messages...")
        #--------------------------------------------------------------------------------

    
    #--------------------------------------------------------------------
    # funktioner til pose:
    def robotPosition(self, msg):
        self.get_logger().info("Received pose data", once=True)
        #orientation:
        ori = msg.pose.pose.orientation
        q = spm.UnitQuaternion([ori.w, ori.x, ori.y, ori.z])
        R = q.R
        np.set_printoptions(precision=4, suppress=True)  # Set print options for better readability
        self.R_base2wrist = spm.SO3(R)

        theta, axis = self.R_base2wrist.angvec()

        rvec = theta * axis

        rx = rvec[0] * 180/math.pi
        ry = rvec[1] * 180/math.pi
        rz = rvec[2] * 180/math.pi

        #position:
        pos = msg.pose.pose.position
        tvec = np.array([[pos.x],[pos.y],[pos.z]], dtype=float)

        print("---------------------------------------------------------------------------")
        print(f"Rotation: x: {rx} y: {ry} z: {rz}")
        print(f"Translation: x: {tvec[0]} y: {tvec[1]} z: {tvec[2]}")
        print("---------------------------------------------------------------------------")
        





def main():
    rclpy.init()
    node = PoseListener()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
