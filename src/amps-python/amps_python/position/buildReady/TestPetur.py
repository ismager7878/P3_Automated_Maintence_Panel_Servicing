import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PoseStamped
from cv_bridge import CvBridge

class ImagePoseListener(Node):
    def __init__(self):
        super().__init__('image_pose_listener')

        # QoS for sensordata (kamera/pose fra bag): ofte BEST_EFFORT og lille depth
        sensor_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST
        )

        self.bridge = CvBridge()

        # Topics fra din bag
        self.sub_color_img = self.create_subscription(
            Image,
            '/camera/camera/color/image_raw',
            self.on_color_image,
            sensor_qos
        )
        self.sub_depth_img = self.create_subscription(
            Image,
            '/camera/camera/depth/image_rect_raw',
            self.on_depth_image,
            sensor_qos
        )
        self.sub_pose = self.create_subscription(
            PoseStamped,
            '/tcp_pose_broadcaster/pose',
            self.on_pose,
            sensor_qos
        )
        self.sub_color_info = self.create_subscription(
            CameraInfo,
            '/camera/camera/color/camera_info',
            self.on_color_info,
            sensor_qos
        )
        self.sub_depth_info = self.create_subscription(
            CameraInfo,
            '/camera/camera/depth/camera_info',
            self.on_depth_info,
            sensor_qos
        )

    def on_color_image(self, msg: Image):
        self.get_logger().info(f'Color image: {msg.width}x{msg.height}, stamp={msg.header.stamp.sec}.{msg.header.stamp.nanosec}')

    def on_depth_image(self, msg: Image):
        self.get_logger().info(f'Depth image: {msg.width}x{msg.height}, stamp={msg.header.stamp.sec}.{msg.header.stamp.nanosec}')

    def on_pose(self, msg: PoseStamped):
        p = msg.pose.position
        self.get_logger().info(f'Pose: ({p.x:.3f}, {p.y:.3f}, {p.z:.3f}), stamp={msg.header.stamp.sec}.{msg.header.stamp.nanosec}')

    def on_color_info(self, msg: CameraInfo):
        self.get_logger().debug(f'Color K: {list(msg.k)}')

    def on_depth_info(self, msg: CameraInfo):
        self.get_logger().debug(f'Depth K: {list(msg.k)}')

def main():
    rclpy.init()
    node = ImagePoseListener()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
