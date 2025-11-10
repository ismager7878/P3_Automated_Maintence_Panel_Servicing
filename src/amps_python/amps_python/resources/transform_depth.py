import cv2 as cv
import numpy as np
from transform_color import sanitize_lines, convert_lines_to_points, calculate_corner_points

def transform_depth(img, max_line_angle_deviation, show=False):
    # Calculate median of ROI
    adjustedImg = np.array(img, dtype=np.uint16)
    vals = adjustedImg[250:350, 250:350]
    median = np.median(vals)
    
    # # Method 1
    # upper_threshold = median + 50
    # lower_threshold = upper_threshold - 256
    # adjustedImg = adjustedImg - lower_threshold

    
    # Method 2
    min_val, max_val = median-26, median+7
    adjustedImg = ((img.astype(np.float32) - min_val) / (max_val - min_val)) * 255
    
    # Clipping
    adjustedImg[adjustedImg < 0] = 0
    adjustedImg[adjustedImg > 255] = 0
    adjustedImg = adjustedImg.astype(np.uint8)
        
     # Segmentation
    lines = cv.HoughLines(adjustedImg, 3, np.deg2rad(1), 200, None, 0, 0).tolist()
    lines = sanitize_lines(lines, max_line_angle_deviation)
    
    # Identification
    points = convert_lines_to_points(img, lines)
    corner_points = calculate_corner_points(points)
    
    # Transformation
    corner_points = np.array(corner_points, dtype="float32")
    dst_points = np.array([[680,930],[680,0],[0,0],[0,930]],dtype="float32")
    transform_matrix = cv.getPerspectiveTransform(corner_points, dst_points)
    warped_img = cv.warpPerspective(adjustedImg, transform_matrix, (680, 930))

    return warped_img, transform_matrix
    
if __name__ == "__main__":
    img = cv.imread('datasets/test_images_dataset/btn_config_1/rosbag2_2025_10_30-14_13_08_0/depth.png', cv.IMREAD_UNCHANGED)
    improved, M = transform_depth(img, np.deg2rad(0.5))
    #improved = cv.dilate(improved, np.ones((4,4), np.uint8), iterations=1)
    improved_colored = cv.applyColorMap(improved, cv.COLORMAP_JET)
    cv.imwrite("datasets/test_images_dataset/btn_config_1/rosbag2_2025_10_30-14_13_08_0/transformed_depth.png", improved_colored)
    cv.imshow("Improved Depth Image", improved_colored)
    cv.waitKey(0)
    cv.destroyAllWindows()