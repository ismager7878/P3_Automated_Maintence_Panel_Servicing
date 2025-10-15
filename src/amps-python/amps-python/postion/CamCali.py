import cv2 as cv
import cv2.aruco as aruco
import numpy as np
import os
import glob

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
