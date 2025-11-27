import csv, os, json
import glob
import natsort

paths = []

dataset_dir = "datasets/auto_aligned_dataset/"
paths = glob.glob(dataset_dir + "*/*/")


paths = natsort.natsorted(paths)

paths_test = [path for i, path in enumerate(paths) if i % 3 == 0]

# Remove test paths from training paths
paths_training = paths.copy()
for path in paths_test:
    paths_training.remove(path)

print("Test Image Paths:")
for path in paths_test:
    print(path)

print("Training Image Paths:")
for path in paths_training:
    print(path)

# Create CSV files and write paths
with open("datasets/auto_aligned_dataset/test_paths.csv", "w", newline='') as test_file:
    csv_writer = csv.writer(test_file)
    for path in paths_test:
        dir_path = os.path.dirname(path)
        csv_writer.writerow([dir_path])

with open("datasets/auto_aligned_dataset/training_paths.csv", "w", newline='') as training_file:
    csv_writer = csv.writer(training_file)
    for path in paths_training:
        dir_path = os.path.dirname(path)
        csv_writer.writerow([dir_path])