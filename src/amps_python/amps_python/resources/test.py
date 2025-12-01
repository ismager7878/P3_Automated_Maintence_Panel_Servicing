import csv, os, json
import numpy as np
import cv2 as cv

# ---------------------- Insert code to be tested here ----------------------


def transform_depth(img, show=False):
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
    binaryImg = cv.medianBlur(binaryImg, 5)
    #binaryImg = cv.morphologyEx(binaryImg, cv.MORPH_CLOSE, kernel)
    #binaryImg = cv.morphologyEx(binaryImg, cv.MORPH_OPEN, kernel)
    if show:
        cv.imshow("Binary Depth Image", binaryImg)
        cv.waitKey(0)
        cv.destroyAllWindows()

    try:
        # Find contours and keep the largest
        contours, _ = cv.findContours(binaryImg, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
        largest = max(contours, key=cv.contourArea)
        #largest = sorted(contours, key=cv.contourArea)

        # Bounding box
        rect = cv.minAreaRect(largest)     # rotated rectangle
        box = cv.boxPoints(rect)           # 4 corner points
        box = np.int32(box)
        box = order_points(box)  # order points: top-left, top-right, bottom-right, bottom-left
    except Exception as ex:
        return None

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
    dst_points = np.array([[0,0],[883,0],[883,681],[0,681]],dtype="float32")
    transform_matrix = cv.getPerspectiveTransform(corner_points, dst_points)
    warped_img = cv.warpPerspective(adjustedImg, transform_matrix, (883, 681))

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



# ---------------------- End of test code ----------------------


# Load image paths from file
#! Is currently set to load training data
color_paths = []
depth_paths = []

print("Reading CSV file")
with open("datasets/auto_aligned_dataset/training_paths.csv", "r") as file:
    csvFile = csv.reader(file)
    for line in csvFile:
        print(f"Reading images in: {line[0]}", end="\r", flush=True)
        color_paths.append(os.path.join(line[0], "color.png"))
        depth_paths.append(os.path.join(line[0], "depth.png"))
print("\nDone reading CSV file")

# Load images from paths
color_images = []
depth_images = []

print("Loading color images")
for i, path in enumerate(color_paths):
    print(f"{i+1} of {len(color_paths)}", end="\r")
    depthImg = cv.imread(path)
    color_images.append(depthImg)
print()

print("Loading depth images")
for i, path in enumerate(depth_paths):
    print(f"{i+1} of {len(depth_paths)}", end="\r")
    depthImg = cv.imread(path, cv.IMREAD_UNCHANGED)
    depth_images.append(depthImg)
print()

#Load ground truths
print("Loading ground truth data")
with open("datasets/test_images_dataset/btn_config_1/ground_truth.json", "r") as json_file:
    ground_truth_btn_config_1 = json.load(json_file)
with open("datasets/test_images_dataset/btn_config_2/ground_truth.json", "r") as json_file:
    ground_truth_btn_config_2 = json.load(json_file)
with open("datasets/test_images_dataset/btn_config_3/ground_truth.json", "r") as json_file:
    ground_truth_btn_config_3 = json.load(json_file)
with open("datasets/test_images_dataset/btn_config_4/ground_truth.json", "r") as json_file:
    ground_truth_btn_config_4 = json.load(json_file)
with open("datasets/test_images_dataset/btn_config_5/ground_truth.json", "r") as json_file:
    ground_truth_btn_config_5 = json.load(json_file)
print("Done loading ground truth data")

if __name__ == "__main__":
    for depthImg, colorImg in zip(depth_images, color_images):
        croppedDepth, M = transform_depth(depthImg, False)
        croppedColor = cv.warpPerspective(colorImg, M, (croppedDepth.shape[1], croppedDepth.shape[0]))
        depthColored = cv.applyColorMap(croppedDepth, cv.COLORMAP_JET)
        cv.imshow("Transformed Color Image", croppedColor)
        cv.imshow("Colored Depth Image", depthColored)
        cv.waitKey(0)
        cv.destroyAllWindows()