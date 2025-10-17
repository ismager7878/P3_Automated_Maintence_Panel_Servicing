#source /opt/ros/jazzy/setup.bash
import cv2 as cv
import cv2.aruco as aruco
import numpy as np
import glob
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class CameraCalibration(Node):

    def __init__(self):
        super().__init__('camera_calibration')
        self.subscription = self.create_subscription(
            #ingen ide,               # message type
            'videoFeed',            # topic name
            self.listener_callback,  # callback function
            10                    # QoS (queue size)
        )
        self.subscription  # prevent unused variable warning

    # cam_cali kan ikke laves før vi har data fra et checker board
    def cam_cali():
        # Antal indre hjørner i dit checkerboard
        CHESSBOARD_SIZE = (9, 6)

        # Reelle fysiske mål for ét kvadrat (i meter eller mm)
        SQUARE_SIZE = 0.025  # 25 mm

        # Klargør objektpunkter (3D punkter i "virkeligheden")
        objp = np.zeros((CHESSBOARD_SIZE[0]*CHESSBOARD_SIZE[1], 3), np.float32)
        objp[:, :2] = np.mgrid[0:CHESSBOARD_SIZE[0], 0:CHESSBOARD_SIZE[1]].T.reshape(-1, 2)
        objp *= SQUARE_SIZE

        # Lister til punkter fra alle billeder
        objpoints = []  # 3D points
        imgpoints = []  # 2D points

        images = glob.glob('calib_images/*.jpg')

        for fname in images:
            img = cv.imread(fname)
            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

            # Find checkerboard corners
            ret, corners = cv.findChessboardCorners(gray, CHESSBOARD_SIZE, None)

            if ret:
                objpoints.append(objp)
                imgpoints.append(corners)

                # (valgfrit) vis hjørner
                cv.drawChessboardCorners(img, CHESSBOARD_SIZE, corners, ret)
                cv.imshow('Corners', img)
                cv.waitKey(100)

        cv.destroyAllWindows()

        ret, cameraMatrix, distCoeffs, rvecs, tvecs = cv.calibrateCamera(
        objpoints, imgpoints, gray.shape[::-1], None, None)

        print("Camera matrix:\n", cameraMatrix)
        print("Distortion coefficients:\n", distCoeffs)

        img = cv.imread('calib_images/img1.jpg')
        h, w = img.shape[:2]
        newCameraMatrix, roi = cv.getOptimalNewCameraMatrix(cameraMatrix, distCoeffs, (w,h), 1, (w,h))
        undistorted = cv.undistort(img, cameraMatrix, distCoeffs, None, newCameraMatrix)
        cv.imshow('Original', img)
        cv.imshow('Undistorted', undistorted)
        cv.waitKey(0)
        cv.destroyAllWindows()

    # handeyeCali skal have data fra både robotten og cameraet.
    def hand_eye_cali():
        #R: rotation
        #t. translation

        R_gripper2base = [np.eye(3),
                          np.eye(3),
                          np.eye(3)]
        
        t_gripper2base = [np.array([[0.0, 0.0, 0.0]]).T,
                          np.array([[0.1, 0.0, 0.0]]).T,
                          np.array([[0.0, 0.1, 0.0]]).T]

        R_target2cam = [np.eye(3),
                        np.eye(3),
                        np.eye(3)]

        t_target2cam = [np.array([[0.0, 0.0, 0.5]]).T,
                        np.array([[0.05, 0.0, 0.5]]).T,
                        np.array([[0.0, 0.05, 0.5]]).T]
        
        #this function outputs in quaternion:
        R_cam2gripper, t_cam2gripper = cv.calibrateHandEye(R_gripper2base, 
                                                            t_gripper2base, 
                                                            R_target2cam, 
                                                            t_target2cam, 
                                                            None, 
                                                            None, 
                                                            cv.CALIB_HAND_EYE_TSAI)

def main(args=None):
    rclpy.init(args=args)
    node = CameraCalibration()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
