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
from std_msgs.msg import Bool
from amps_cpp.msg import ProgramState


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

        #-------------------------------------------------------------------------------
        # Subscribtions:
        
        # Subscriber til kamera feed
        color_topic = self.get_parameter('color_topic').get_parameter_value().string_value
        self.sub_image = self.create_subscription(
            Image,
            color_topic,
            self.image_callback,
            sensor_qos
        )

        # Subscriber til ProgramState
        self.sub_program_state = self.create_subscription(
            ProgramState,
            'amps/program_state',
            self.program_state_callback,
            10
        )

        # Subscribe til is_board_reachable
        self.is_board_reachable = False  # Track state
        self.sub_is_board_reachable = self.create_subscription(
            Bool,
            "amps_cpp/pose_estimation/is_board_reachable",
            self.is_board_reachable_callback,
            10
        )
        #-------------------------------------------------------------------------------

        #Publisher:
        self.pub_state = self.create_publisher(ProgramState, 'amps/program_state', 10)


        #Sætter ProgramState til start position
        self.setProgramState(ProgramState.FINDING_PANEL)

    #----------------------------------------------------------------------------------------
    #Call backs:
    def image_callback(self, msg: Image):
        """Callback from ROS Image topic. Convert to OpenCV image and store for GUI update."""
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            # store latest image for GUI thread to pick up
            self.latest_image = cv_image
        except Exception as e:
            self.get_logger().warn(f"Failed to convert image: {e}")

    def program_state_callback(self, msg: ProgramState):
        """Callback for ProgramState messages."""
        self.current_program_state = msg.state
        self.get_logger().info(f"Program state changed to: {msg.state_str}")

    def is_board_reachable_callback(self, msg: Bool):
        """Callback for is_board_reachable messages."""
        self.is_board_reachable = msg.data
        self.get_logger().info(f"Board reachable: {msg.data}")

    #---------------------------------------------------------------------------------------    

    def setProgramState(self, state: int, state_str: str = ""):
        msg = ProgramState()
        msg.state = state
        msg.state_str = state_str
        self.pub_state.publish(msg)


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
        #self.buttonNextAction.setFixedSize(50, 20)
        #self.buttonNextAction.setStyleSheet
        self.buttonNextAction.clicked.connect(self.NextProccesStep)

        # Current status viser:
        self.status_label = QLabel("Status bar")
        self.status_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.status_label.setStyleSheet("background-color: black; color : white")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)# Create label, set size and align
        self.status_label.setFixedHeight(50)
        self.status_label.setStyleSheet(f"background-color: gray; color : white")


        # Image display label
        self.image_label = QLabel("No image yet")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(640, 360)
        self.image_label.setStyleSheet("""QLabel {border: 5px solid gray;border-radius: 10px;background-color: black;}""")
        
        #----------------------------------------------------------------
        # Strukturer layout:
        layout.addWidget(self.image_label)

        layout.addWidget(self.status_label)

        layout.addWidget(self.buttonNextAction) #sætter knappen på bunden
        #----------------------------------------------------------------

        self.setLayout(layout)
        # Timer to spin ROS and update image
        if self.node is not None:
            self.ros_timer = QTimer(self)
            self.ros_timer.timeout.connect(self._ros_spin_and_update)
            self.ros_timer.start(50)  # 20 Hz

    def NextProccesStep(self):
        self.node.setProgramState(ProgramState.APPROACHING_PANEL)

    def _ros_spin_and_update(self):
        # Process ROS callbacks
        try:
            rclpy.spin_once(self.node, timeout_sec=0)
        except Exception:
            pass

        # Update button enable/disable based on board reachability
        if hasattr(self.node, 'is_board_reachable'):
            self.buttonNextAction.setEnabled(self.node.is_board_reachable)

        # Update border color based on program state
        self._update_status_text()
        self._update_border_color()

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

    def _update_status_text(self):
        state = self.node.current_program_state
      
        #---------------------------------------------------------------
        #Show state in lable
        if state == 1:
            self.status_label.setText("FINDING PANEL")

        if state == 2:
            self.status_label.setText("APPROACHING PANEL")

        if state == 3:
            self.status_label.setText("SERVICING PANEL")

        if state == 4:
            self.status_label.setText("RETREATING")

        if state == 5:
            self.status_label.setText("MISSION COMPLETE")

        if state == 0:
            self.status_label.setText("MANUAL CONTROL")

        if state == -1:
            self.status_label.setText("ERROR")
        #---------------------------------------------------------------
    
    def _update_border_color(self):
        """Update the image label border color based on program state."""
        if not hasattr(self.node, 'current_program_state'):
            return

        state = self.node.current_program_state

        reach = self.node.is_board_reachable

        if state == ProgramState.MANUAL_CONTROL:
            self.image_label.setStyleSheet(f"""QLabel {{border: 5px solid orange; border-radius: 10px; background-color: black;}}""")
        
        elif state == ProgramState.FINDING_PANEL and reach == False:
            self.image_label.setStyleSheet(f"""QLabel {{border: 5px solid red; border-radius: 10px; background-color: black;}}""")

        elif state == ProgramState.FINDING_PANEL and reach == True:
            self.image_label.setStyleSheet(f"""QLabel {{border: 5px solid green; border-radius: 10px; background-color: black;}}""")
        
        else:
            # Define color mapping for each state
            color_map = {
                ProgramState.APPROACHING_PANEL: "green",
                ProgramState.SERVICING_PANEL: "green",
                ProgramState.RETREATING: "green",
                ProgramState.MISSION_COMPLETE: "blue",
                ProgramState.ERROR_STATE: "red"
            }
            
            color = color_map.get(state, "gray")
            self.image_label.setStyleSheet(f"""QLabel {{border: 5px solid {color}; border-radius: 10px; background-color: black;}}""")

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
    