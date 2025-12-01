from transform_depth import transform_depth
import csv, os, json
import numpy as np
import cv2 as cv

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