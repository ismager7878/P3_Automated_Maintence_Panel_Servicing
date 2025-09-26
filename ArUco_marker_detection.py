#https://automaticaddison.com/how-to-perform-pose-estimation-using-an-aruco-marker/
#Petur Hammer
import cv2 as cv
import numpy as np
import matplotlib as plt
import os
import glob


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
    distorted_image = cv.imread("Iphone_cali\cal-img(2).jpg")

    cv.imshow("distorted image", distorted_image)
    cv.waitKey(0)
    cv.destroyAllWindows()

    # Perform camera calibration to return the camera matrix, distortion coefficients, rotation and translation vectors etc 
    ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(object_points, 
                                                        image_points, 
                                                        gray.shape[::-1], 
                                                        None, 
                                                        None)

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

    cv.imshow("undistorted", undistorted_image)
    # Display the window until any key is pressed
    cv.waitKey(0) 
    # Close all windows
    cv.destroyAllWindows()

cam_cali()