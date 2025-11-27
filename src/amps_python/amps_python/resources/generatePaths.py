import csv, os, json
import glob
import natsort

color_paths = []
depth_paths = []

dataset_dir = "datasets/auto_aligned_dataset/"
files = glob.glob(dataset_dir + "*/*/*.png")

for file in files:
    if "color" in file:
        color_paths.append(file)
    elif "depth" in file:
        depth_paths.append(file)

color_paths = natsort.natsorted(color_paths)
depth_paths = natsort.natsorted(depth_paths)

color_paths_test = [path for i, path in enumerate(color_paths) if i % 3 == 0]
depth_paths_test = [path for i, path in enumerate(depth_paths) if i % 3 == 0]

# Remove test paths from training paths
color_paths_training = color_paths.copy()
for path in color_paths_test:
    color_paths_training.remove(path)
depth_paths_training = depth_paths.copy()
for path in depth_paths_test:
    depth_paths_training.remove(path)

print("Test Color Image Paths:")
for path in color_paths_test:
    print(path)

print("Training Color Image Paths:")
for path in color_paths_training:
    print(path)