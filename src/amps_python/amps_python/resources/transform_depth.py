import cv2 as cv
import numpy as np
from transform_color import sanitize_lines, convert_lines_to_points, calculate_corner_points

def transform_depth(img, max_line_angle_deviation, show=False):
    # Calculate median of ROI
    adjustedImg = np.array(img, dtype=np.uint16)
    vals = adjustedImg[280:780, 70:570]
    median_of_roi = np.median(vals)
    
    # Scaling
    min_val, max_val = median_of_roi-26, median_of_roi+7
    adjustedImg = ((img.astype(np.float32) - min_val) / (max_val - min_val)) * 255
    
    # Clipping
    adjustedImg[adjustedImg < 0] = 0
    adjustedImg[adjustedImg > 255] = 0
    adjustedImg = adjustedImg.astype(np.uint8)
    if show:
        cv.imshow("Adjusted Depth Image", adjustedImg)
        cv.waitKey(0)
        cv.destroyAllWindows()
        
    # Segmentation
    _, binaryImg = cv.threshold(adjustedImg, 1, 255, cv.THRESH_BINARY)
    kernel = np.ones((21,21), np.uint8)
    binaryImg = cv.medianBlur(binaryImg, 5)
    #binaryImg = cv.morphologyEx(binaryImg, cv.MORPH_CLOSE, kernel)
    #binaryImg = cv.morphologyEx(binaryImg, cv.MORPH_OPEN, kernel)
    if show:
        cv.imshow("Binary Depth Image", binaryImg)
        cv.waitKey(0)
        cv.destroyAllWindows()

    # Find contours and keep the largest
    contours, _ = cv.findContours(binaryImg, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
    largest = max(contours, key=cv.contourArea)
    largest = sorted(contours, key=cv.contourArea)

    # Bounding box
    rect = cv.minAreaRect(largest)     # rotated rectangle
    box = cv.boxPoints(rect)           # 4 corner points
    box = np.int32(box)
    box = order_points(box)  # order points: top-left, top-right, bottom-right, bottom-left

    # Draw corner points and lines
    if show:
        print("Corner Points:\n", box)
        print(box[0])
        adjustedImgBGR = cv.cvtColor(adjustedImg, cv.COLOR_GRAY2BGR)
        cv.polylines(adjustedImgBGR, [box.astype(np.int32)], True, (0,255,0), 3)
        cv.imshow("Corner Points and lines", adjustedImgBGR)
        cv.waitKey(0)
        cv.destroyAllWindows()

    
    # Transformation
    corner_points = np.array(box, dtype="float32")
    dst_points = np.array([[684,0],[684,861],[0,861],[0,0]],dtype="float32")
    transform_matrix = cv.getPerspectiveTransform(corner_points, dst_points)
    warped_img = cv.warpPerspective(adjustedImg, transform_matrix, (684, 861))

    return warped_img, transform_matrix

def order_points(points):
    box = np.zeros((4,2), dtype="float32")

    sum = points.sum(axis=1)
    box[0] = points[np.argmin(sum)]     # top-left
    box[2] = points[np.argmax(sum)]     # bottom-right

    diff = np.diff(points, axis=1)
    box[1] = points[np.argmin(diff)]  # top-right
    box[3] = points[np.argmax(diff)]  # bottom-left

    return box # return the ordered coordinates like: top-left, top-right, bottom-right, bottom-left
    
if __name__ == "__main__":
    img = cv.imread('datasets/auto_aligned_dataset/button_pose1/img4_0/depth.png', cv.IMREAD_UNCHANGED)
    improved, M = transform_depth(img, np.deg2rad(0.5), True)
    print("Transformation Matrix:\n", M)
    #improved = cv.dilate(improved, np.ones((4,4), np.uint8), iterations=1)
    improved_colored = cv.applyColorMap(improved, cv.COLORMAP_JET)
    #cv.imwrite("datasets/auto_aligned_dataset/button_pose1/img4_0/transformed_depth.png", improved_colored)
    cv.imshow("Improved Depth Image", improved_colored)
    cv.waitKey(0)
    cv.destroyAllWindows()