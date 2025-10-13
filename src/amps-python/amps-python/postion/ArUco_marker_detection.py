#https://automaticaddison.com/how-to-perform-pose-estimation-using-an-aruco-marker/
#Petur Hammer
import cv2 as cv
import numpy as np
import matplotlib as plt
import os
import glob
import roboticstoolbox as rbt
from spatialmath import UnitQuaternion
 

def arUco_corner_detection():
    img = cv.imread("ArUco-tavle_vinkel.jpg")

    
    img_resize = cv.resize(img, (768,1024))
   
    # Converter billede til grayscale, som detectmarker skal bruge
    gray = cv.cvtColor(img_resize, cv.COLOR_BGR2GRAY)

    # Predefiner hvilket aruco bibliotek aruco markerne er lavet fra
    aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_5X5_1000)
    parameters = cv.aruco.DetectorParameters()

    # ArUco detector
    detector = cv.aruco.ArucoDetector(aruco_dict, parameters)
    # Detect the markers
    corners, ids, rejected = detector.detectMarkers(gray)
    # Print the detected markers
    print("Detected markers:", ids)
    if ids is not None:
        print("Corner position:",corners)
        cv.aruco.drawDetectedMarkers(img_resize, corners, ids)
        cv.imshow("Detected Markers",img_resize)
        cv.waitKey(0)
        cv.destroyAllWindows()

def cam_cali():
    # Chessboard dimensions
    number_of_squares_X = 8 # Number of chessboard squares along the x-axis
    number_of_squares_Y = 8  # Number of chessboard squares along the y-axis
    nX = number_of_squares_X - 1 # Number of interior corners along x-axis
    nY = number_of_squares_Y - 1 # Number of interior corners along y-axis
    square_size = 0.0248 # Lenght of the side of a square in the chess board pattern
    

    # Store vectors of 3D points for all chessboard images (world coordinate frame)
    object_points = []
    
    # Store vectors of 2D points for all chessboard images (camera coordinate frame)
    image_points = []
    
    # Set termination criteria. We stop either when an accuracy is reached or when
    # we have finished a certain number of iterations.
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    
    # Define real world coordinates for points in the 3D coordinate frame
    # Object points are (0,0,0), (1,0,0), (2,0,0) ...., (5,8,0)
    object_points_3D = np.zeros((nX * nY, 3), np.float32)       
    
    # These are the x and y coordinates                                              
    object_points_3D[:,:2] = np.mgrid[0:nY, 0:nX].T.reshape(-1, 2) 
    
    object_points_3D = object_points_3D * square_size

    # Image path
    image = cv.imread("Chess_cali\cal-img(2).jpg")

    # Convert the image to grayscale
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)  

    # Find the corners on the chessboard
    success, corners = cv.findChessboardCorners(gray, (nY, nX), None)

    if success == True:

        # Append object points
        object_points.append(object_points_3D)

        # Find more exact corner pixels       
        corners_2 = cv.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)       
        
        # Append image points
        image_points.append(corners_2)

        
        # Draw the corners
        cv.drawChessboardCorners(image, (nY, nX), corners, success)
        # resize image for display
        img_resize = cv.resize(image, (768,1024))
        # Display the image 
        cv.imshow("Image", img_resize) 
        # Display the window until any key is pressed
        #cv.waitKey(0) 
        # Close all windows
        #cv.destroyAllWindows()
        
        

            # Now take a distorted image and undistort it 
    distorted_image = cv.imread("Chess_cali\cal-img(2).jpg")

    # Perform camera calibration to return the camera matrix, distortion coefficients, rotation and translation vectors etc 
    ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(object_points, image_points, gray.shape[::-1], None, None)

    # Get the dimensions of the image 
    height, width = distorted_image.shape[:2]
        
    # Refine camera matrix
    # Returns optimal camera matrix and a rectangular region of interest
    optimal_camera_matrix, roi = cv.getOptimalNewCameraMatrix(mtx, dist, 
                                                                (width,height), 
                                                                1, 
                                                                (width,height))

    # Undistort the image
    undistorted_image = cv.undistort(distorted_image, mtx, dist, None, 
                                        optimal_camera_matrix)
    
    und_img_resize = cv.resize(undistorted_image, (768,1024))

    # Crop the image. Uncomment these two lines to remove black lines
    # on the edge of the undistorted image.
    #x, y, w, h = roi
    #undistorted_image = undistorted_image[y:y+h, x:x+w]

    # Display key parameter outputs of the camera calibration process
    print("image")
    
    print("Optimal Camera matrix:") 
    print(optimal_camera_matrix) 

    print("\n Distortion coefficient:") 
    print(dist) 

    print("\n Rotation Vectors:") 
    print(rvecs) 

    print("\n Translation Vectors:") 
    print(tvecs) 

    cv.imshow("undistorted", und_img_resize)
    # Display the window until any key is pressed
    cv.waitKey(0) 
    # Close all windows
    cv.destroyAllWindows()

def quaternion2RPY(w,x,y,z):
    q = UnitQuaternion([w, x, y, z])
    # RPY (ZYX) from quaternion
    rpy = q.rpy(unit='rad')    
    print("RPY:",rpy) 
    

def arUco_pose():
# ArUco info:
#----------------------------------------------------------------------------------------------------------------------------
    #ArUco library name
    arUco_lib = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_5X5_1000)
    # ArUco size in meters
    arUco_size = 0.076
#----------------------------------------------------------------------------------------------------------------------------
# Camera calibration info
#----------------------------------------------------------------------------------------------------------------------------
    # Camera matrix comes from cam_cali
    camera_matrix = np.array([[2.24161385e+03, 0, 5.99485425e+02],
                            [0, 1.84002016e+03, 9.65142764e+02],
                            [0, 0, 1]])    
    # Distortion coefficient come from cam_cali
    distortion_coefficient = np.array([0.48337895, -3.11487545, -0.01358789, -0.03477453,  3.9685751])
#----------------------------------------------------------------------------------------------------------------------------
# her skal video filen
    cap = 1

    while(True):
    
        # Capture frame-by-frame
        # This method returns True/False as well
        # as the video frame.
        ret, frame = cap.read()  
        
        # Detect ArUco markers in the video frame
        (corners, marker_ids, rejected) = cv.aruco.detectMarkers(frame, this_aruco_dictionary, parameters=this_aruco_parameters,cameraMatrix=mtx, distCoeff=dst)
        
        # Check that at least one ArUco marker was detected
        if marker_ids is not None:
    
        # Draw a square around detected markers in the video frame
            cv.aruco.drawDetectedMarkers(frame, corners, marker_ids)
        
        # Get the rotation and translation vectors
        rvecs, tvecs, obj_points = cv.aruco.estimatePoseSingleMarkers(corners,0.076,mtx,dst)
            
        # Print the pose for the ArUco marker
        # The pose of the marker is with respect to the camera lens frame.
        # Imagine you are looking through the camera viewfinder, 
        # the camera lens frame's:
        # x-axis points to the right
        # y-axis points straight down towards your toes
        # z-axis points straight ahead away from your eye, out of the camera
        for i, marker_id in enumerate(marker_ids):
        
            # Store the translation (i.e. position) information
            transform_translation_x = tvecs[i][0][0]
            transform_translation_y = tvecs[i][0][1]
            transform_translation_z = tvecs[i][0][2]
    
            # Store the rotation information
            rotation_matrix = np.eye(4)
            rotation_matrix[0:3, 0:3] = cv.Rodrigues(np.array(rvecs[i][0]))[0]
            r = R.from_matrix(rotation_matrix[0:3, 0:3])
            quat = r.as_quat()   
            
            # Quaternion format     
            transform_rotation_x = quat[0] 
            transform_rotation_y = quat[1] 
            transform_rotation_z = quat[2] 
            transform_rotation_w = quat[3] 
            
            # Euler angle format in radians
            roll_x, pitch_y, yaw_z = euler_from_quaternion(transform_rotation_x, 
                                                        transform_rotation_y, 
                                                        transform_rotation_z, 
                                                        transform_rotation_w)
            
            roll_x = math.degrees(roll_x)
            pitch_y = math.degrees(pitch_y)
            yaw_z = math.degrees(yaw_z)
            print("transform_translation_x: {}".format(transform_translation_x))
            print("transform_translation_y: {}".format(transform_translation_y))
            print("transform_translation_z: {}".format(transform_translation_z))
            print("roll_x: {}".format(roll_x))
            print("pitch_y: {}".format(pitch_y))
            print("yaw_z: {}".format(yaw_z))
            print()
            
            # Draw the axes on the marker
            cv.aruco.drawAxis(frame, mtx, dst, rvecs[i], tvecs[i], 0.05)
        
            # Display the resulting frame
            cv.imshow('frame',frame)
            
            # If "q" is pressed on the keyboard, 
            # exit this loop
            if cv.waitKey(1) & 0xFF == ord('q'):
                break
    
        # Close down the video stream
        cap.release()
        cv.destroyAllWindows()


