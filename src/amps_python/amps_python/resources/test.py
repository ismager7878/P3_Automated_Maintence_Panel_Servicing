from transform_color import transformed_color
from transform_depth import improve_depth_image
import csv, os, json
import numpy as np
import cv2 as cv

# Load image paths from file
#! Is currently set to load training data
color_paths = []
depth_paths = []

print("Reading CSV file")
with open("datasets/test_images_dataset/training_paths.csv", "r") as file:
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
    img = cv.imread(path)
    color_images.append(img)
print()

print("Loading depth images")
for i, path in enumerate(depth_paths):
    print(f"{i+1} of {len(depth_paths)}", end="\r")
    img = cv.imread(path, cv.IMREAD_UNCHANGED)
    depth_images.append(img)
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
    for img in depth_images:
        improved = improve_depth_image(img)
        # improved = cv.erode(improved, np.ones((9,9), np.uint8), iterations=1)
        improved = cv.dilate(improved, np.ones((4,4), np.uint8), iterations=1)
        improved_colored = cv.applyColorMap(improved, cv.COLORMAP_JET)
        cv.imshow("Improved Depth Image", improved_colored)
        cv.waitKey(0)
        cv.destroyAllWindows()