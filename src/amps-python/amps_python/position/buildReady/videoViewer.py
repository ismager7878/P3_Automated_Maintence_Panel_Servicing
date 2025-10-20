#Chat genereret til test
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class VideoViewer(Node):
    def __init__(self):
        super().__init__('video_viewer')

        # Parametre (du kan override dem fra CLI)
        self.declare_parameter('color_topic', '/camera/camera/color/image_raw')
        self.declare_parameter('depth_topic', '/camera/camera/depth/image_rect_raw')
        self.declare_parameter('use_depth', False)  # sæt True for at vise depth

        self.bridge = CvBridge()
        sensor_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST
        )

        if self.get_parameter('use_depth').get_parameter_value().bool_value:
            topic = self.get_parameter('depth_topic').get_parameter_value().string_value
            self.sub = self.create_subscription(Image, topic, self.on_depth, sensor_qos)
            self.get_logger().info(f'Viser DEPTH fra: {topic}')
        else:
            topic = self.get_parameter('color_topic').get_parameter_value().string_value
            self.sub = self.create_subscription(Image, topic, self.on_color, sensor_qos)
            self.get_logger().info(f'Viser COLOR fra: {topic}')

        # Timer til at håndtere cv2.waitKey uden at blokere rclpy
        self.timer = self.create_timer(0.001, self.on_timer)

    def on_color(self, msg: Image):
        try:
            # typisk encoding: "bgr8" eller "rgb8" -> cv_bridge håndterer det
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            cv2.imshow('Color', frame)
        except Exception as e:
            self.get_logger().warn(f'Kunne ikke konvertere farvebillede: {e}')

    def on_depth(self, msg: Image):
        try:
            depth = self.bridge.imgmsg_to_cv2(msg)  # ofte 16UC1
            # Normalisér og farvelæg for visning
            depth_float = depth.astype('float32')
            depth_float[depth_float == 0] = float('nan')  # maskér 0’er hvis ønsket
            # Vælg et fornuftigt max-range (justér efter dit kamera, fx 4000 mm)
            max_mm = 4000.0
            norm = cv2.normalize(depth_float, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U, mask=(depth_float>0))
            colored = cv2.applyColorMap(norm, cv2.COLORMAP_TURBO)
            cv2.imshow('Depth', colored)
        except Exception as e:
            self.get_logger().warn(f'Kunne ikke konvertere depth-billede: {e}')

    def on_timer(self):
        # Luk på ESC eller q
        k = cv2.waitKey(1) & 0xFF
        if k in (27, ord('q')):
            self.get_logger().info('Lukker vinduer…')
            cv2.destroyAllWindows()
            rclpy.shutdown()

def main():
    rclpy.init()
    node = VideoViewer()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        if rclpy.ok():
            rclpy.shutdown()
