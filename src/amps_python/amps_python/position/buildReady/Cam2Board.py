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

class Cam2Board(Node):
    def __init__(self):
        super().__init__('Cam2Board')

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


    #--------------------------------------------------------------------
    def is_pose_different_enough(self, R_new, t_new):
        """Check if new pose is sufficiently different from recent poses"""
        if len(self.R_w2b) == 0:
            return True
        
        # Check against last 5 poses
        check_count = min(5, len(self.R_w2b))
        for i in range(1, check_count + 1):
            R_old = self.R_w2b[-i]
            t_old = self.t_w2b[-i]
            
            # Check translation difference
            t_diff = np.linalg.norm(t_new - t_old)
            
            # Check rotation difference (Frobenius norm)
            R_diff = np.linalg.norm(R_new - R_old, 'fro')
            
            # If too similar to any recent pose, reject
            if t_diff < self.min_translation_diff and R_diff < self.min_rotation_diff:
                return False
        
        return True
    
    #--------------------------------------------------------------------
    # funktioner til pose:
    def quaternion2rotationMatrix(self, msg):
        self.get_logger().info("Received pose data", once=True)
        #orientation:
        ori = msg.pose.pose.orientation
        q = spm.UnitQuaternion([ori.w, ori.x, ori.y, ori.z])
        R = q.R
        np.set_printoptions(precision=4, suppress=True)  # Set print options for better readability
        self.R_base2wrist = spm.SO3(R)

        #position:
        pos = msg.pose.pose.position
        self.t_base2wrist = np.array([[pos.x],[pos.y],[pos.z]], dtype=float)

    #--------------------------------------------------------------------
    #funktioner til video:
    def on_timer(self):
        # Luk på ESC eller q
        k = cv2.waitKey(1) & 0xFF
        if k in (27, ord('q')):
            self.get_logger().info('Lukker vinduer…')
            cv2.destroyAllWindows()
            rclpy.shutdown()

   
    #skal bruges til når vi skifter over til aruco pose estimation
    def dict_finder(self, msg: FrameWithPose):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg.frame, desired_encoding="bgr8")

            
            #Alle aruco dictionaries i opencv:
            #-------------------------------------------------------------------
            arucoDict4x4 = aruco.getPredefinedDictionary(aruco.DICT_4X4_1000)
            arucoDict5x5 = aruco.getPredefinedDictionary(aruco.DICT_5X5_1000)
            arucoDict6x6 = aruco.getPredefinedDictionary(aruco.DICT_6X6_1000)
            arucoDict7x7 = aruco.getPredefinedDictionary(aruco.DICT_7X7_1000)
            #-------------------------------------------------------------------

            libStorage = [arucoDict4x4, arucoDict5x5, arucoDict6x6, arucoDict7x7] 

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            for i in range(len(libStorage)):
                parameters = aruco.DetectorParameters_create()
                corner, ids, rejected = aruco.detectMarkers(gray, libStorage[i], parameters = parameters)
                
                if ids is not None and len(ids) > 2 and i == 0:
                    print("4x4 library is a match")    
                    return libStorage[i]
                
                if ids is not None and len(ids) > 2 and i == 1:
                    print("5x5 library is a match")
                    return libStorage[i]
                
                if ids is not None and len(ids) > 2 and i == 3:
                    print("6x6 library is a match")
                    return libStorage[i]
                
                if ids is not None and len(ids) > 2 and i == 4:
                    print("7x7 library is a match")
                    return libStorage[i]
            
            print("No matches found")
        
        except Exception as e:
            self.get_logger().warn(f'Kunne ikke konvertere farvebillede: {e}')
    
    def cam2boardMatrixes(self, msg: FrameWithPose):
        self.get_logger().info("Received frame_with_pose message", once=True)
        
        #-------------------------------------------------------------
        # First, extract pose data from the message
        # msg.pose is a PoseStamped, so we need msg.pose.pose.orientation
        ori = msg.pose.pose.orientation
        q = spm.UnitQuaternion([ori.w, ori.x, ori.y, ori.z])
        R = q.R
        self.R_base2wrist = spm.SO3(R)
        
        pos = msg.pose.pose.position
        self.t_base2wrist = np.array([[pos.x],[pos.y],[pos.z]], dtype=float)
        
        # Debug: log first pose to check units
        self.get_logger().info(f"Robot pose (x,y,z): ({pos.x:.4f}, {pos.y:.4f}, {pos.z:.4f})", once=True)
        

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
           
            retval, rvec, tvec = cv2.solvePnP(objectPoints, imagePoints, self.K, self.D)
            self.R_board2cam, _ = cv2.Rodrigues(rvec)
            self.t_board2cam = tvec

            #-------------------------------------------------------------
            # Prepare robot pose
            if retval == True:
                R_b2w = self.R_base2wrist.R                 # numpy 3x3
                t_b2w = self.t_base2wrist

                # invertér: T_g2b = (T_b2g)^-1
                R_w2b = R_b2w.T
                t_w2b = -R_b2w.T @ t_b2w
                
                # Check if this pose is different enough from recent poses
                if self.is_pose_different_enough(R_w2b, t_w2b):
                    # Save both board→cam and wrist→base transformations
                    self.R_b2c.append(self.R_board2cam)
                    self.t_b2c.append(self.t_board2cam)
                    self.R_w2b.append(R_w2b)  
                    self.t_w2b.append(t_w2b)
                    
                    if len(self.R_b2c) % 10 == 0:  # Print every 10 samples
                        self.get_logger().info(f"Samples collected: {len(self.R_b2c)}")
                else:
                    self.get_logger().info("Pose too similar to recent samples, skipping...", throttle_duration_sec=1.0)

            #-------------------------------------------------------------
            cv2.imshow("corners", image)
        #if len(self.R_b2c) < 400:   
            #print(f"image list lenght: {len(self.R_b2c)}")
            #print(f"current R_pose: {self.R_base2wrist}")
            #print(f"current t_pose: {self.t_base2wrist} ")
        
        if len(self.R_b2c) == 50:
            print("calibrating")
            R_c2g, t_c2g = cv2.calibrateHandEye(
            self.R_w2b, self.t_w2b,
            self.R_b2c, self.t_b2c,
            method=cv2.CALIB_HAND_EYE_TSAI)

            print("translation:")
            print(t_c2g)
            print("Rotation:")
            print(R_c2g)

            #print("translation board2cam:")
            #print(self.t_b2c)

            print("calculation on 50 samples")

        if len(self.R_b2c) == 70:
            print("calibrating")
            R_c2g, t_c2g = cv2.calibrateHandEye(
            self.R_w2b, self.t_w2b,
            self.R_b2c, self.t_b2c,
            method=cv2.CALIB_HAND_EYE_TSAI)

            print("translation:")
            print(t_c2g)
            print("Rotation:")
            print(R_c2g)

            print("calculation on 70 samples")

        if len(self.R_b2c) == 400:
            print("calibrating")
            R_c2g, t_c2g = cv2.calibrateHandEye(
            self.R_w2b, self.t_w2b,
            self.R_b2c, self.t_b2c,
            method=cv2.CALIB_HAND_EYE_TSAI)

            print("translation:")
            print(t_c2g)
            print("Rotation:")
            print(R_c2g)

            print("all done :)")
            


def main():
    rclpy.init()
    node = Cam2Board()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        if rclpy.ok():
            rclpy.shutdown()
