import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from cv_bridge import CvBridge
import cv2
import cv2.aruco as aruco
import numpy as np
import xml.etree.ElementTree as ET
import os
from ament_index_python.packages import get_package_share_directory
#from geometry_msgs.msg import PoseStamped
import spatialmath as spm
from amps_cpp.msg import FrameWithPose
import math

class BoardTest(Node):
    def __init__(self):
        super().__init__('BoardTest')

        self.get_logger().info(f"OpenCV version: {cv2.__version__}")

        # Parametre (du kan override dem fra CLI)
        self.declare_parameter('color_topic', '/camera/camera/color/image_raw')

        self.bridge = CvBridge()
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
            self.cam2boardMatrixes,
            10
        )
        self.get_logger().info("Subscribed to 'amps_cpp/pose_estimation/rgb_frame_with_pose' topic. Waiting for messages...")
        #--------------------------------------------------------------------------------

        # Timer til at håndtere cv2.waitKey uden at blokere rclpy
        self.timer = self.create_timer(0.001, self.on_timer)

        #-------------------------------------------------------------
        # Find calibration XML file from installed package share directory
        try:
            pkg_share = get_package_share_directory('amps_python')
            xml = os.path.join(pkg_share, 'data', 'calibration-data', 'cam_calibration.xml')
            xml_factory = os.path.join(pkg_share, 'data', 'calibration-data', 'factory_settings.xml')
        except Exception as e:
            self.get_logger().error(f"Could not find package share directory: {e}")
            raise
        
        if not os.path.exists(xml):
            self.get_logger().error(f"Calibration file not found: {xml}")
            raise FileNotFoundError(f"Calibration file not found: {xml}")
        
        
        
        tree = ET.parse(xml)
        root = tree.getroot()
        self.K = np.array(root.find('camera_matrix/data').text.split(), float).reshape(3,3)
        self.D = np.array(root.find('distortion_coefficients/data').text.split(), float).reshape(1,5)

        
        #---------------------------------------------------------------
        # stop the iteration when specified
        # accuracy, epsilon, is reached or
        # specified number of iterations are completed.
        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        #----------------------------------------------------------------
        #lister til at gemme transformationer:
        self.R_w2b = []  # wrist->base
        self.t_w2b = []
        self.R_b2c = []  # board->camera
        self.t_b2c = []
        
        # Initialize pose variables (will be set when first message arrives)
        self.R_base2wrist = None
        self.t_base2wrist = None
        
        # Sample filtering parameters
        self.min_translation_diff = 0.03  # 3cm minimum movement
        self.min_rotation_diff = 0.08     # ~5 degrees minimum rotation change

    #funktioner til video:
    def on_timer(self):
        # Luk på ESC eller q
        k = cv2.waitKey(1) & 0xFF
        if k in (27, ord('q')):
            self.get_logger().info('Lukker vinduer…')
            cv2.destroyAllWindows()
            rclpy.shutdown()

    def cam2boardMatrixes(self, msg: FrameWithPose):
        self.get_logger().info("Received frame_with_pose message", once=True)
        
        #-------------------------------------------------------------
        #load image as frame from the FrameWithPose message
        frame = self.bridge.imgmsg_to_cv2(msg.frame, desired_encoding="bgr8")
        #-------------------------------------------------------------
        # Define chess board size:
        pattern_size = (7, 7)  # antal indre hjørner
        square_size = 0.025    # 25 mm = 0.025 m
        #-------------------------------------------------------------
        # generér 3D-punkterne for alle hjørner i (x,y,z)
        objectPoints = np.zeros((pattern_size[0]*pattern_size[1], 3), np.float32)
        objectPoints[:, :2] = np.mgrid[0:pattern_size[0],
                                    0:pattern_size[1]].T.reshape(-1, 2)
        objectPoints *= square_size
        #-------------------------------------------------------------
        # opencv funktion til at finde image points
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        ret, corners = cv2.findChessboardCorners(gray, pattern_size)
        if ret:
            # Forbedr nøjagtigheden
            corners = cv2.cornerSubPix(
                gray, corners, (11, 11), (-1, -1),
                (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            )

            # Refining pixel coordinates
            # for given 2d points.
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)

            # Draw and display the corners
            image = cv2.drawChessboardCorners(gray, pattern_size, corners2, ret)

            imagePoints = corners2
            #-------------------------------------------------------------
            # camera til board vektor og matrise
            # Use the correct calibration matrices based on dist_cali flag
           
            retval, rvec, tvec = cv2.solvePnP(objectPoints, imagePoints, self.K, self.D)
            self.R_board2cam, _ = cv2.Rodrigues(rvec)
            self.t_board2cam = tvec

            rotx = rvec[0] * 180/math.pi
            roty = rvec[1] * 180/math.pi
            rotz = rvec[2] * 180/math.pi

            axis = np.float32([[3,0,0], [0,3,0], [0,0,-3]])
            imgpts, jac = cv2.projectPoints(axis, rvec, tvec, self.K, self.D)


            #-------------------------------------------------------------
            def draw(img, corners, imgpts):
                # Convert corner and projected points to integer tuples for cv2
                c = np.array(corners[0]).ravel()
                corner = (int(round(float(c[0]))), int(round(float(c[1]))))

                def to_pt(p):
                    a = np.array(p).ravel()
                    return (int(round(float(a[0]))), int(round(float(a[1]))))

                p0 = to_pt(imgpts[0])
                p1 = to_pt(imgpts[1])
                p2 = to_pt(imgpts[2])

                img = cv2.line(img, corner, p0, (255,0,0), 5)
                img = cv2.line(img, corner, p1, (0,255,0), 5)
                img = cv2.line(img, corner, p2, (0,0,255), 5)
                return img

            img = draw(frame.copy(), corners2, imgpts)

            cv2.imshow("corners", img)
            print(f"rotation: x: {rotx} y: {roty} z: {rotz}")
            
        
        

def main():
    rclpy.init()
    node = BoardTest()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        if rclpy.ok():
            rclpy.shutdown()