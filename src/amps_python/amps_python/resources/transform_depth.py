import cv2 as cv
import numpy as np
from transform_color import sanitize_lines, convert_lines_to_points, calculate_corner_points

calibration_matrix_depth = np.array([[384.3314208984375, 0.0, 321.20361328125],
                                     [0.0, 384.3314208984375, 235.78701782226562],
                                     [0.0, 0.0, 1.0]])

distortion_coefficients_depth = np.array([0, 0, 0, 0, 0])

def transform_depth(img, max_line_angle_deviation, show=False):
    img = cv.undistort(img, calibration_matrix_depth, distortion_coefficients_depth)
    # Calculate median of ROI
    adjustedImg = np.array(img, dtype=np.uint16)
    vals = adjustedImg[250:350, 250:350]
    most_freq_val = np.bincount(vals.flatten()).argmax()
    
    # # Method 1
    # upper_threshold = median + 50
    # lower_threshold = upper_threshold - 256
    # adjustedImg = adjustedImg - lower_threshold

    
    # Scaling
    min_val, max_val = most_freq_val-26, most_freq_val+7
    adjustedImg = ((img.astype(np.float32) - min_val) / (max_val - min_val)) * 255
    
    # Clipping
    adjustedImg[adjustedImg < 0] = 0
    adjustedImg[adjustedImg > 255] = 0
    adjustedImg = adjustedImg.astype(np.uint8)
    cv.imshow("Adjusted Depth Image", adjustedImg)
    cv.waitKey(0)
    cv.destroyAllWindows()
        
     # Segmentation
    canny = cv.Canny(adjustedImg, 100, 200, L2gradient=True)
    lines = cv.HoughLines(canny, 3, np.deg2rad(1), 200, None, 0, 0).tolist()
    lines = sanitize_lines(lines, max_line_angle_deviation)
    
    # Identification
    points = convert_lines_to_points(img, lines)
    corner_points = calculate_corner_points(points)

    # Draw corner points and lines
    if show:
        print("Corner Points:", corner_points)
        adjustedImgBGR = cv.cvtColor(adjustedImg, cv.COLOR_GRAY2BGR)
        cv.circle(adjustedImgBGR, corner_points[0], 15, (255,0,255), -1)
        cv.circle(adjustedImgBGR, corner_points[1], 15, (255,0,255), -1)
        cv.circle(adjustedImgBGR, corner_points[2], 15, (255,0,255), -1)
        cv.circle(adjustedImgBGR, corner_points[3], 15, (255,0,255), -1)
        cv.line(adjustedImgBGR, corner_points[0], corner_points[1], (0,255,0), 4)
        cv.line(adjustedImgBGR, corner_points[1], corner_points[2], (0,255,0), 4)
        cv.line(adjustedImgBGR, corner_points[2], corner_points[3], (0,255,0), 4)
        cv.line(adjustedImgBGR, corner_points[3], corner_points[0], (0,255,0), 4)        
        cv.imshow("Corner Points and lines", adjustedImgBGR)
        cv.waitKey(0)
        cv.destroyAllWindows()

    
    # Transformation
    corner_points = np.array(corner_points, dtype="float32")
    dst_points = np.array([[684,861],[684,0],[0,0],[0,861]],dtype="float32")
    transform_matrix = cv.getPerspectiveTransform(corner_points, dst_points)
    warped_img = cv.warpPerspective(adjustedImg, transform_matrix, (684, 861))

    return warped_img, transform_matrix
    
if __name__ == "__main__":
    img = cv.imread('datasets/test_images_dataset/btn_config_1/rosbag2_2025_10_30-14_13_08_0/depth.png', cv.IMREAD_UNCHANGED)
    improved, M = transform_depth(img, np.deg2rad(0.5), True)
    print("Transformation Matrix:\n", M)
    #improved = cv.dilate(improved, np.ones((4,4), np.uint8), iterations=1)
    improved_colored = cv.applyColorMap(improved, cv.COLORMAP_JET)
    #cv.imwrite("datasets/test_images_dataset/btn_config_1/rosbag2_2025_10_30-14_13_08_0/transformed_depth.png", improved_colored)
    cv.imshow("Improved Depth Image", improved_colored)
    cv.waitKey(0)
    cv.destroyAllWindows()
