import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from cv_bridge import CvBridge
import cv2
import numpy as np
import xml.etree.ElementTree as ET
import os
from ament_index_python.packages import get_package_share_directory
from amps_cpp.msg import FrameWithPose  # antager at msg.frame er sensor_msgs/Image
import spatialmath as spm
import threading
import yaml

class Handeye(Node):
    def __init__(self):
        super().__init__('Handeye')
        self.get_logger().info(f"OpenCV version: {cv2.__version__}")
        
        # Use simple highgui backend to avoid Qt threading issues
        cv2.namedWindow("RGB (press 's' to save, 'q'/ESC to quit)", cv2.WINDOW_NORMAL)

        # Params
        self.declare_parameter('color_topic', '/camera/camera/color/image_raw')

        self.bridge = CvBridge()

        # QoS til sensor data (best effort + keep last)
        sensor_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST
        )
        
        # Subscriber til pose data for snapper funktionen
        self.sub_pose = self.create_subscription(
            FrameWithPose,
            'amps_cpp/pose_estimation/rgb_frame_with_pose',
            self.snapper,
            sensor_qos
        )
        self.get_logger().info("Subscribed to 'amps_cpp/pose_estimation/rgb_frame_with_pose'…")

        # Timer til UI/keyboard (ikke blokér ROS)
        self.timer = self.create_timer(0.01, self.on_timer)

        # --- Load calibration (K, D)
        try:
            pkg_share = get_package_share_directory('amps_python')
            xml = os.path.join(pkg_share, 'data', 'calibration-data', 'cam_calibration.xml')
        except Exception as e:
            self.get_logger().error(f"Could not find package share directory: {e}")
            raise

        if not os.path.exists(xml):
            raise FileNotFoundError(f"Calibration file not found: {xml}")

        root = ET.parse(xml).getroot()
        self.K = np.array(root.find('camera_matrix/data').text.split(), float).reshape(3,3)
        self.D = np.array(root.find('distortion_coefficients/data').text.split(), float).reshape(1,5)

        self.get_logger().info(f"Camera intrinsics K:\n{self.K}")
        self.get_logger().info(f"Distortion coefficients D: {self.D}")

        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        # --- Buffere og state
        self.image = None
        self.img_pose = None  # Billede med tegnet pose
        self.save_requested = False
        self.calculate = False
        self.cal_handeye = False
        self.corner_detection = False
        self.save_yaml = False

        self.saved_oris = []  # liste af np.array([w,x,y,z])
        self.saved_pos  = []  # liste af np.array([x,y,z])
        self.saved_imgs = []  # liste af BGR billeder (np.ndarray)
        self.saved_rotmat = []

        self.saved_cam_oris = []
        self.saved_cam_pos = []

        self.logger = self.get_logger()

        self._lock = threading.Lock()

        #--- variabler til calibrering
        self.x = 0
        self.y = 0
        self.z = 0
        self.roll = 0
        self.pitch = 0
        self.yaw = 0

    #---------------------------------------------------------------------------------------------------------------

    def on_timer(self):
        # Vis billede kun hvis vi har modtaget et

        if self.img_pose is not None:
            cv2.imshow("RGB (press 's' to save, 'q'/ESC to quit)", self.img_pose)

        k = cv2.waitKey(1) & 0xFF
        
        if k == ord('s') and self.corner_detection == True:
            self.save_requested = True  # gem næste modtagne frame
            self.logger.info(f"rob pose: {len(self.saved_pos)}, frame: {len(self.saved_imgs)}")

        if k == ord("s") and self.corner_detection == False:
            self.logger.info("No corners found")
        
        if k == ord("b"):
            self.calculate = True # kører kamera kinematik funktion
            self.generate_img_kinematic()
            self.calculate = False

        if k == ord("h"):
            self.cal_handeye = True # kører handeye funktion  
            self.handEye()
            self.cal_handeye = False

        if k == ord("g"):
            self.save_yaml = True # vis tilfredsstillende, gem data i yaml fil
            self.save_yaml()
            self.save_yaml = False

        elif k in (ord('q'), 27):  # q eller ESC
            self.get_logger().info('Lukker vinduer…')
            cv2.destroyAllWindows()
            rclpy.shutdown()
    #---------------------------------------------------------------------------------------------------------------
   
    # funktioner bliver brugt til at gemme billede, roation og position fra robot
    def snapper(self, msg: FrameWithPose):
        q = msg.pose.pose.orientation
        p = msg.pose.pose.position
        ori = np.array([q.w, q.x, q.y, q.z], dtype=np.float64)
        pos = np.array([p.x, p.y, p.z], dtype=np.float64)

        try:
            self.image  = self.bridge.imgmsg_to_cv2(msg.frame, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().warn(f"Failed to convert image: {e}")
            return

        frame = self.image

        # 3) Hvis bruger har trykket 's', gem denne frame + pose
        if self.save_requested:
            with self._lock:
                self.saved_imgs.append(frame.copy())
                #konverter quaternion til roatationsmatrix
                ori_c = ori.copy()
                q = spm.UnitQuaternion([ori_c[0], ori_c[1], ori_c[2], ori_c[3]])
                R = q.R
                np.set_printoptions(precision=4, suppress=True)  # Set print options for better readability
                R_base2wrist = spm.SO3(R)

                self.saved_rotmat.append(R_base2wrist)
                self.saved_pos.append(pos.copy())
                self.saved_oris.append(ori.copy())
                self.save_requested = False
                
                # Debug logging
                self.get_logger().info(f"=== Gemt sample #{len(self.saved_imgs)} ===")
                self.get_logger().info(f"Robot position [m]: X={pos[0]:.4f}, Y={pos[1]:.4f}, Z={pos[2]:.4f}")
                self.get_logger().info(f"Robot quaternion: w={ori[0]:.4f}, x={ori[1]:.4f}, y={ori[2]:.4f}, z={ori[3]:.4f}")
            
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

        self.corner_detection = False

        ret, corners = cv2.findChessboardCorners(gray, pattern_size)
        if ret:
            # Forbedr nøjagtigheden
            self.corner_detection = True
            corners = cv2.cornerSubPix(
                gray, corners, (11, 11), (-1, -1),
                (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            )

            # Refining pixel coordinates
            # for given 2d points.
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)

            # Draw and display the corners
            image_w_corners = cv2.drawChessboardCorners(gray, pattern_size, corners2, ret)

            imagePoints = corners2.reshape(-1, 2).astype(np.float32)
            #-------------------------------------------------------------
            # camera til board vektor and matrise
            # Use the correct calibration matrices based on dist_cali flag
           
            retval, rvec, tvec =  cv2.solvePnP(objectPoints, imagePoints, self.K, self.D)
            
            
            self.R_board2cam, _ = cv2.Rodrigues(rvec)
            self.t_board2cam = tvec

            s = square_size
            axis = np.float32([[s,0,0], [0,s,0], [0,0,-s]])
            imgpts, jac = cv2.projectPoints(axis, rvec, tvec, self.K, self.D)

            #-------------------------------------------------------------
            def draw(img, corners, imgpts):
                # Convert corner and projected points to integer tuples for cv2
                c = np.array(corners[0]).ravel()
                corner = (int(round(float(c[0]))), int(round(float(c[1]))))

                #self.logger.info(f"rotation: x: {rotx} y: {roty} z: {rotz}")
                def to_pt(p):
                    a = np.array(p).ravel()
                    return (int(round(float(a[0]))), int(round(float(a[1]))))

                p0 = to_pt(imgpts[0])
                p1 = to_pt(imgpts[1])
                p2 = to_pt(imgpts[2])

                img = cv2.line(img, corner, p0, (0,0,255), 5)   # X=rød
                img = cv2.line(img, corner, p1, (0,255,0), 5)   # Y=grøn
                img = cv2.line(img, corner, p2, (255,0,0), 5)   # Z=blå
                return img

            self.img_pose = draw(frame.copy(), corners2[0], imgpts)

    def generate_img_kinematic(self):
        if self.calculate == True:
            self.logger.info("Calculating kinematics")
            for i in range(len(self.saved_imgs)):
                frame = self.saved_imgs[i]
                    
                # Define chess board size:
                pattern_size = (7, 7)  # antal indre hjørner
                square_size = 0.025    # 25 mm = 0.025 m
                #-------------------------------------------------------------
                # generér 3D-punkterne for alle hjørner i (x,y,z)
                objectPoints = np.zeros((pattern_size[0]*pattern_size[1], 3), np.float32)
                objectPoints[:, :2] = np.mgrid[0:pattern_size[0],
                                            0:pattern_size[1]].T.reshape(-1, 2)
                objectPoints *= square_size
                
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
                    image_w_corners = cv2.drawChessboardCorners(gray, pattern_size, corners2, ret)

                    imagePoints = corners2.reshape(-1, 2).astype(np.float32)
                    #-------------------------------------------------------------
                    # camera til board vektor og matrise
                    # Use the correct calibration matrices based on dist_cali flag
                
                    retval, rvec, tvec =  cv2.solvePnP(objectPoints, imagePoints, self.K, self.D)
                    
                    
                    R_board2cam, _ = cv2.Rodrigues(rvec)
                    t_board2cam = tvec.reshape(3, 1)  # Ensure (3,1) shape

                    self.saved_cam_oris.append(R_board2cam)
                    self.saved_cam_pos.append(t_board2cam)
                    
                    # Debug logging for board→cam transform
                    # Note: OpenCV chessboard frame: origin at top-left corner, X right, Y down, Z towards camera
                    self.logger.info(f"Sample {i}: board→cam translation [m]: X={t_board2cam[0][0]:.4f}, Y={t_board2cam[1][0]:.4f}, Z={t_board2cam[2][0]:.4f}")
        self.logger.info("------------------------------------------------------------------------")
        self.logger.info(f"img pose: {len(self.saved_cam_pos)} img rot: {len(self.saved_cam_oris)}")
        self.logger.info(f"rob pose: {len(self.saved_pos)} rob rot: {len(self.saved_oris)}")
        self.logger.info(f"rotation matrix; {len(self.saved_rotmat)}")
        self.logger.info("------------------------------------------------------------------------")

    def handEye(self):
        if self.cal_handeye == True:
            self.logger.info(f"Number of samples - cam: {len(self.saved_cam_pos)}, robot: {len(self.saved_pos)}")
            if len(self.saved_cam_oris) == len(self.saved_cam_pos) == len(self.saved_pos) == len(self.saved_rotmat):
                
                # Prepare lists for calibrateHandEye
                # IMPORTANT: Testing showed that WITHOUT inversion gives correct results!
                # This suggests the pose from /tcp_pose_broadcaster/pose is already in the correct frame
                R_gripper2base_list = []
                t_gripper2base_list = []
                
                for i in range(len(self.saved_rotmat)):
                    # Use pose directly without inversion
                    R = self.saved_rotmat[i].R
                    t = self.saved_pos[i].reshape(3, 1)
                    
                    R_gripper2base_list.append(R)
                    t_gripper2base_list.append(t)
                    
                # Log first sample for verification
                self.logger.info(f"Sample 0: R_g2b shape={R_gripper2base_list[0].shape}, t_g2b shape={t_gripper2base_list[0].shape}")
                self.logger.info(f"Sample 0: R_target2cam shape={self.saved_cam_oris[0].shape}, t_target2cam shape={self.saved_cam_pos[0].shape}")
                
                # Check diversity of samples (important for good calibration)
                if len(self.saved_pos) >= 2:
                    max_trans_diff = 0
                    max_rot_diff = 0
                    for i in range(len(self.saved_pos)):
                        for j in range(i+1, len(self.saved_pos)):
                            trans_diff = np.linalg.norm(self.saved_pos[i] - self.saved_pos[j])
                            rot_diff = np.linalg.norm(self.saved_rotmat[i].R - self.saved_rotmat[j].R, 'fro')
                            max_trans_diff = max(max_trans_diff, trans_diff)
                            max_rot_diff = max(max_rot_diff, rot_diff)
                    
                    self.logger.info(f"Sample diversity: max translation diff = {max_trans_diff:.4f} m, max rotation diff = {max_rot_diff:.4f}")
                    if max_trans_diff < 0.05:
                        self.logger.warn("WARNING: Robot poses are very similar (< 5cm). Move robot more between samples!")
                    if max_rot_diff < 0.1:
                        self.logger.warn("WARNING: Robot orientations are very similar. Rotate robot more between samples!")
                
                
                # Log some transforms to verify correctness
                self.logger.info("=== Verifying transform directions ===")
                self.logger.info(f"First robot pose (base→gripper): t={self.saved_pos[0]}")
                self.logger.info(f"After inversion (gripper→base): t={t_gripper2base_list[0].flatten()}")
                self.logger.info(f"First board→cam: t={self.saved_cam_pos[0].flatten()}")
                
                self.logger.info("Running hand-eye calibration...")
                # calibrateHandEye(R_gripper2base[], t_gripper2base[], R_target2cam[], t_target2cam[])
                # Returns: R_cam2gripper, t_cam2gripper
                R_cam2gripper, t_cam2gripper = cv2.calibrateHandEye(
                    R_gripper2base_list, t_gripper2base_list,
                    self.saved_cam_oris, self.saved_cam_pos,
                    method=cv2.CALIB_HAND_EYE_TSAI)
                
                # Convert rotation matrix to RPY for easier interpretation
                so = spm.SO3(R_cam2gripper)
                roll, pitch, yaw = so.rpy(unit='rad')
                
                self.x = t_cam2gripper[0][0]
                self.y = t_cam2gripper[1][0]
                self.z = t_cam2gripper[2][0]
                self.roll = roll
                self.pitch = pitch
                self.yaw = yaw


                self.logger.info("========================================================================")
                self.logger.info("Hand-Eye Calibration Result (Camera→TCP/Flange):")
                self.logger.info("------------------------------------------------------------------------")
                self.logger.info(f"Translation [m]: X={t_cam2gripper[0][0]:.4f}, Y={t_cam2gripper[1][0]:.4f}, Z={t_cam2gripper[2][0]:.4f}")
                self.logger.info(f"Translation norm: {np.linalg.norm(t_cam2gripper):.4f} m")
                self.logger.info(f"Rotation [rad]: Roll={roll:.2f}, Pitch={pitch:.2f}, Yaw={yaw:.2f}")
                self.logger.info("------------------------------------------------------------------------")
                self.logger.info(f"Rotation Matrix:\n{R_cam2gripper}")
                self.logger.info("========================================================================")


            else:
                self.logger.info("transformation arrays are not the same lenght :(")

    def save_yaml(self):
        package_name = 'amps_python'  

        # Find share folder for package og opbyg stien til config
        pkg_share = get_package_share_directory(package_name)
        config_dir = os.path.join(pkg_share, 'data')
        #os.makedirs(config_dir, exist_ok=True)   # opret folder hvis den ikke findes

        yaml_path = os.path.join(config_dir, 'handeye.yaml')

        data_wildcard = {
            "/**": {
                "ros__parameters": {
                "camera_to_gripper": {
                "translation": [self.x, self.y, self.z],
                "rotation": [self.roll, self.pitch, self.yaw],
                "frame_id": "tool0",
                "child_frame_id": "camera",
                    }
                }
            }
        }

        
        data_to_write = data_wildcard  

        # Skriv YAML til fil
        with open(yaml_path, 'w') as f:
            yaml.safe_dump(data_to_write, f, default_flow_style=False)

        self.logger.info(f"YAML file saved: {yaml_path}")

            


def main():
    rclpy.init()
    node = Handeye()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        if rclpy.ok():
            rclpy.shutdown()
