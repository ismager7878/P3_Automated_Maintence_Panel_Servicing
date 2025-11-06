import cv2 as cv
import numpy as np

def transformed_color(img, max_line_angle_deviation, show=False):
    # Preprocessing
    imgHSV = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    mask = cv.inRange(imgHSV, (0, 0, 120), (255, 77, 255))
    mask = cv.medianBlur(mask, 9)
    imgMasked = cv.bitwise_and(img, img, mask=mask)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    grayMasked = cv.cvtColor(imgMasked, cv.COLOR_BGR2GRAY)
    canny = cv.Canny(gray, 100, 200, L2gradient=True)

    # Segmentation
    lines = cv.HoughLines(canny, 3, np.deg2rad(1), 200, None, 0, 0).tolist()
    lines = sanitize_lines(lines, max_line_angle_deviation)
    
    # Identification
    points = convert_lines_to_points(img, lines)
    corner_points = calculate_corner_points(points)
    
    # Draw corner points
    if show:
        cv.circle(img, corner_points[0], 10, (255,0,0), -1)
        cv.circle(img, corner_points[1], 10, (0,255,0), -1)
        cv.circle(img, corner_points[2], 10, (0,0,255), -1)
        cv.circle(img, corner_points[3], 10, (255,255,0), -1)
        
    # Transformation
    corner_points = np.array(corner_points, dtype="float32")
    dst_points = np.array([[680,930],[680,0],[0,0],[0,930]],dtype="float32")
    transform_matrix = cv.getPerspectiveTransform(corner_points, dst_points)
    warped_img = cv.warpPerspective(img, transform_matrix, (680, 930))
    if show:
        imshow(warped_img)
    return warped_img, transform_matrix

def sanitize_lines(lines, max_line_angle_deviation):
    """Returns: (horizontals, verticals, others)"""
    horizontals = []
    verticals = []
    others = []
    # Only keep lines that are not close to horizontal or vertical
    for i in range(len(lines)):
        theta = lines[i][0][1]
        if (abs(theta - 0) < max_line_angle_deviation or abs(theta - np.pi) < max_line_angle_deviation):
            verticals.append(lines[i][0])
        elif (abs(theta - np.pi/2) < max_line_angle_deviation or abs(theta - 3*np.pi/2) < max_line_angle_deviation):
            horizontals.append(lines[i][0])
        else:
            others.append(lines[i][0])
            
    return horizontals, verticals, others

def convert_lines_to_points(img, lines):
    points = ([],[],[])
    # Convert lines from polar to cartesian for easier processing
    for category in range(len(lines)):
        if lines is not None:  
            for line in range(len(lines[category])):
                rho = lines[category][line][0]
                theta = lines[category][line][1]
                a = np.cos(theta)
                b = np.sin(theta)
                x0 = a * rho
                y0 = b * rho
                pt1 = (int(x0 + 10000*(-b)), int(y0 + 10000*(a)))
                pt2 = (int(x0 - 10000*(-b)), int(y0 - 10000*(a)))
                
                # Cap all values to be within image bounds
                pt1 = (max(0, min(pt1[0], img.shape[1]-1)), max(0, min(pt1[1], img.shape[0]-1)))
                pt2 = (max(0, min(pt2[0], img.shape[1]-1)), max(0, min(pt2[1], img.shape[0]-1)))
                
                # Add line points to list
                points[category].append((pt1, pt2))
    return points

def calculate_corner_points(points):    
    # Sort points by horizontal and vertical positions
    horizontals = points[0]
    verticals = points[1]
    horizontals = sorted(horizontals, key=lambda point: (point[0][1], point[1][1]))
    verticals = sorted(verticals, key=lambda point: (point[0][0], point[1][0]))

    border_lines = []
    border_lines.append(horizontals[0])
    border_lines.append(verticals[0])
    border_lines.append(horizontals[-1])
    border_lines.append(verticals[-1])

    corners = []
    for i in range(len(border_lines)):
        intersection = calculate_intersection(border_lines[i], border_lines[i-1])
        if intersection is not None:
            corners.append(intersection)
    return corners

def calculate_intersection(line1, line2):
    x1, y1 = line1[0]
    x2, y2 = line1[1]
    x3, y3 = line2[0]
    x4, y4 = line2[1]

    denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denominator == 0:
        return None  # Lines are parallel

    px = ((x1*y2 - y1*x2)*(x3 - x4) - (x1 - x2)*(x3*y4 - y3*x4)) / denominator
    py = ((x1*y2 - y1*x2)*(y3 - y4) - (y1 - y2)*(x3*y4 - y3*x4)) / denominator
    return int(px), int(py)

def imshow(img):
    cv.imshow('Image', img)
    cv.waitKey(0)
    cv.destroyAllWindows()

if __name__ == "__main__":
    img = cv.imread('datasets/test_images_dataset/btn_config_1/rosbag2_2025_10_30-14_13_08_0/color.png')
    transformed_color(img, np.deg2rad(0.5), show=True)
