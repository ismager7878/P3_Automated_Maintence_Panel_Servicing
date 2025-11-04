import cv2 as cv
import numpy as np

def detect_border(img, show=False):
    imgHSV = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    mask = cv.inRange(imgHSV, (0, 0, 120), (255, 77, 255))
    mask = cv.medianBlur(mask, 9)
    img = cv.bitwise_and(img, img, mask=mask)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    imshow(gray)
    canny = cv.Canny(gray, 100, 200)
    imshow(canny)
    contours, hierarchy = cv.findContours(canny, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)


    contours = sorted(contours, key=cv.contourArea, reverse=True)
    border_contour1 = contours[0]
    border_contour2 = contours[1]
    epsilon1 = 0.02 * cv.arcLength(border_contour1, True)
    epsilon2 = 0.02 * cv.arcLength(border_contour2, True)
    approx1 = cv.approxPolyDP(border_contour1, epsilon1, True)
    approx2 = cv.approxPolyDP(border_contour2, epsilon2, True)
    
    if show:
        img_copy = img.copy()
        cv.drawContours(img_copy, [approx1], -1, (0, 255, 0), 3)
        cv.drawContours(img_copy, [approx2], -1, (0, 255, 0), 3)
        imshow(img_copy)
    return 0

def imshow(img):
    cv.imshow('Image', img)
    cv.waitKey(0)
    cv.destroyAllWindows()

if __name__ == "__main__":
    img = cv.imread('datasets/test_images_dataset/btn_config_1/rosbag2_2025_10_30-14_13_08_0/color.png')
    border_points = detect_border(img, show=True)
    print("Detected border points:", border_points)