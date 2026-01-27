import os
import numpy as np
from sklearn.decomposition import PCA


def find_workspace_root(start_path):
    current = start_path
    while current != "/":
        if "src" in os.listdir(current) and "install" in os.listdir(current):
            return current
        current = os.path.abspath(os.path.join(current, ".."))
    raise RuntimeError("Workspace root not found")


BASE_DIR = os.path.dirname(os.path.realpath(__file__))
WORKSPACE_ROOT = find_workspace_root(BASE_DIR)

folder = os.path.join(WORKSPACE_ROOT, "datasets", "KNN_scaler_data")

labels = np.load(os.path.join(folder, "labels.npy"))
features = np.load(os.path.join(folder, "features.npy"))

# Labels for scalar features (8 features)
scalar_labels = ['std_depth', 'std_intensity', 'min_hue', 'max_hue', 'area', 'HW_ratio', 'min_value', 'max_value']

# Labels for histogram bins (8 bins for hue histogram)
histogram_labels = [f'hue_hist_bin_{i}' for i in range(8)]

# Combined labels matching all_features structure
feature_labels = scalar_labels + histogram_labels

print(f"Loaded {features.shape[0]} samples with {features.shape[1]} features each.")
print(f"Labels shape: {labels.shape}")






