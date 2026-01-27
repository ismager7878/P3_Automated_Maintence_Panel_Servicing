from pca_analysis import run_pca
from lda_analysis import run_lda
from feature_ranking import score_features
from plotting import plot_pca_vs_lda, plot_pca_vs_lda_subplots, plot_recall_ablation, plot_lda_2d, plot_pca_2d
from ablation_analysis import ablation_per_class_recall
import os
import numpy as np
import pandas as pd

def find_workspace_root(start_path):
    current = start_path
    while current != "/":
        if "src" in os.listdir(current) and "install" in os.listdir(current):
            return current
        current = os.path.abspath(os.path.join(current, ".."))
    raise RuntimeError("Workspace root not found")

def compute_within_class_variance(X_transformed, y):
    """Compute average within-class variance"""
    variances = []
    for cls in np.unique(y):
        mask = y == cls
        class_data = X_transformed[mask]
        if len(class_data) > 1:
            variance = np.var(class_data, axis=0).sum()
            variances.append(variance)
    return np.mean(variances)

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
WORKSPACE_ROOT = find_workspace_root(BASE_DIR)

folder = os.path.join(WORKSPACE_ROOT, "datasets", "KNN_scaler_data")

labels = np.load(os.path.join(folder, "labels.npy"))
features = np.load(os.path.join(folder, "features.npy"))

# Labels for scalar features (8 features)
scalar_labels = ['std_depth', 'std_intensity', 'min_hue', 'max_hue', 'area', 'HW_ratio', 'min_value', 'max_value']

feature_types = ['depth_derived'] + ['rgb_derived_scalar'] * 7 + ['rgb_histogram'] * 8

# Labels for histogram bins (8 bins for hue histogram)
histogram_labels = [f'hue_hist_bin_{i}' for i in range(8)]

# Combined labels matching all_features structure
feature_labels = scalar_labels + histogram_labels


# Inputs
X = features                 # shape (n, 16)
y = labels            # shape (n,)
feature_names = feature_labels  # length 16

def main():
    _, pca_results = run_pca(X, feature_names)
    _, lda_results = run_lda(X, y, feature_names)

    # PCA dimension reduction to 2D for visualization
    X_pca_2d, pca_2d_results = run_pca(X, feature_names, n_components=2)

    # LDA dimension reduction to 2D for visualization
    X_lda_2d, lda_2d_results = run_lda(X, y, feature_names, n_components=2)

    df = score_features(pca_results, lda_results, feature_types)
    print(df)

    # Diagnostics
    print(f"\n=== Data Statistics ===")
    print(f"Number of samples: {X.shape[0]}")
    print(f"Number of features: {X.shape[1]}")
    print(f"Number of classes: {len(np.unique(y))}")
    unique, counts = np.unique(y, return_counts=True)
    print(f"Class distribution:")
    for cls, count in zip(unique, counts):
        print(f"  Class {cls}: {count} samples")
    print(f"\nPCA: Variance explained by first 2 PCs: {pca_2d_results['explained_variance_ratio'].sum()*100:.1f}%")
    print(f"LDA: Number of discriminants found: {X_lda_2d.shape[1]}")

    # Within-class variance for each method
    from sklearn.metrics import pairwise_distances_argmin_min

    pca_within_var = compute_within_class_variance(X_pca_2d, y)
    lda_within_var = compute_within_class_variance(X_lda_2d, y)

    print(f"\nWithin-class variance:")
    print(f"  PCA 2D: {pca_within_var:.4f}")
    print(f"  LDA 2D: {lda_within_var:.4f}")
    print(f"  Ratio (LDA/PCA): {lda_within_var/pca_within_var:.4f}")
    print("  → LDA should have LOWER within-class variance\n")

    # Plot 2D PCA projection
    plot_pca_2d(X_pca_2d, y, lda_results["class_labels"], pca_2d_results["explained_variance_ratio"])

    # Plot 2D LDA projection
    plot_lda_2d(X_lda_2d, y, lda_results["class_labels"])

    plot_pca_vs_lda_subplots(
        df,
        class_labels=lda_results["class_labels"]
    )

    df = df.reset_index(drop=True)

    ### Validation ###


    lda_col = f"lda_class_{lda_results['class_labels'][0]}"

    feature_order = (
        df.sort_values(lda_col, ascending=True)
            .index
            .to_numpy()
    )

    print("Feature ranking for ablation study:")
    print(feature_order)

    folder = os.path.join(WORKSPACE_ROOT, "datasets", "Feature_Evaluation_Order")
    
    os.makedirs(folder, exist_ok=True)

    #Save as csv
    pd.DataFrame(feature_order).to_csv(os.path.join(folder, "feature_ablation_order.csv"), index=False, header=False)

if __name__ == "__main__":
    main()


