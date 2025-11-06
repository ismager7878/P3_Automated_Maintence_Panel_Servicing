from border_detector_color import detect_border, calculate_intersection
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
    img = cv.imread(path)
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
    for image in color_images:
        detect_border(image, True)