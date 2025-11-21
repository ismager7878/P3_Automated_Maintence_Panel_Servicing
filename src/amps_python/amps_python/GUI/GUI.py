# source .venv/bin/activate
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QVBoxLayout, QComboBox
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSplitter, QStackedWidget, QLineEdit, QDialog, QDialogButtonBox
from PyQt6.QtGui import QFont, QImage, QPixmap
from PyQt6.QtCore import Qt, QTimer
import PyQt6.QtWidgets as QtW
import sys
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from cv_bridge import CvBridge
import cv2
from sensor_msgs.msg import Image


class GUI_node(Node):
    def __init__(self):
        super().__init__("GUI_node")

        # Params
        self.declare_parameter('color_topic', '/camera/camera/color/image_raw')

        self.bridge = CvBridge()
        self.latest_image = None

        # QoS til sensor data (best effort + keep last)
        sensor_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST
        )
        
        # Subscriber til kamera feed
        color_topic = self.get_parameter('color_topic').get_parameter_value().string_value
        self.sub_image = self.create_subscription(
            Image,
            color_topic,
            self.image_callback,
            sensor_qos
        )

        self.status_running = "green"
        self.status_error   = "orange"

    def image_callback(self, msg: Image):
        """Callback from ROS Image topic. Convert to OpenCV image and store for GUI update."""
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            # store latest image for GUI thread to pick up
            self.latest_image = cv_image
        except Exception as e:
            self.get_logger().warn(f"Failed to convert image: {e}")



    def runGUI(self):
        # Run the GUI and pass a reference to this node
        window = MainWindow(node=self)
        window.runUI()


class MainWindow(QWidget):
    app = QApplication(sys.argv)
    def __init__(self, node: GUI_node = None, title = "Den er lavet med python"):
        super().__init__()
        self.node = node
        self.initUI()
        self.setMinimumSize(730,420)
        self.setWindowTitle(title)

    def initUI(self):
        layout = QVBoxLayout()

        self.buttonNextAction = QPushButton("Next action")
        layout.addWidget(self.buttonNextAction)

        # Image display label
        self.image_label = QLabel("No image yet")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(640, 360)
        layout.addWidget(self.image_label)

        # Status color box
        self.status_box = QPushButton("")
        self.status_box.setStyleSheet("background-color: green; color : green")
        self.status_box.setFixedSize(660, 380)
        layout.addWidget(self.status_box)

        
        self.setLayout(layout)
        # Timer to spin ROS and update image
        if self.node is not None:
            self.ros_timer = QTimer(self)
            self.ros_timer.timeout.connect(self._ros_spin_and_update)
            self.ros_timer.start(50)  # 20 Hz

    def _ros_spin_and_update(self):
        # Process ROS callbacks
        try:
            rclpy.spin_once(self.node, timeout_sec=0)
        except Exception:
            pass

        # If there's a latest image, convert and show it
        img = None
        if hasattr(self.node, 'latest_image') and self.node.latest_image is not None:
            img = self.node.latest_image

        if img is not None:
            # img is expected as a BGR numpy array from cv_bridge
            try:
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            except Exception:
                rgb = img
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb.data.tobytes(), w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pix = QPixmap.fromImage(qt_image).scaled(self.image_label.width(), self.image_label.height(), Qt.AspectRatioMode.KeepAspectRatio)
            self.image_label.setPixmap(pix)

    def runUI(self):
        self.show()
        self.app.exec()

def main():
    rclpy.init()
    node = GUI_node()
    node.runGUI()
    # Note: rclpy.spin() would block the GUI, so we don't use it here
    # The GUI event loop will run instead
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
    