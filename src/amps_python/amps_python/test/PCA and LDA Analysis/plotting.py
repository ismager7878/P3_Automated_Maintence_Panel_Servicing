import matplotlib.pyplot as plt

def plot_pca_vs_lda(df, lda_column="lda_mean"):
    plt.figure()

    for ftype in df["feature_type"].unique():
        subset = df[df["feature_type"] == ftype]
        plt.scatter(
            subset["pca_score"],
            subset[lda_column],
            label=ftype,
            alpha=0.8
        )

        for _, row in subset.iterrows():
            plt.text(
                row["pca_score"],
                row[lda_column],
                row["feature"],
                fontsize=8
            )

    plt.xlabel("PCA score (variance / redundancy)")
    plt.ylabel("LDA score (discriminative power)")
    plt.title(f"PCA vs LDA ({lda_column})")
    plt.legend()
    plt.tight_layout()
    plt.show()


import matplotlib.pyplot as plt
import numpy as np

def plot_pca_vs_lda_subplots(df, class_labels, annotate=True):
    n_classes = len(class_labels)

    fig, axes = plt.subplots(
        1, n_classes,
        figsize=(5 * n_classes, 5),
        sharex=True,
        sharey=True
    )

    if n_classes == 1:
        axes = [axes]

    for ax, cls in zip(axes, class_labels):
        lda_col = f"lda_class_{cls}"

        for ftype in df["feature_type"].unique():
            subset = df[df["feature_type"] == ftype]

            ax.scatter(
                subset["pca_score"],
                subset[lda_col],
                label=ftype,
                alpha=0.8
            )

            if annotate:
                for _, row in subset.iterrows():
                    ax.text(
                        row["pca_score"],
                        row[lda_col],
                        row["feature"],
                        fontsize=8
                    )

        ax.set_title(f"Class {cls}")
        ax.set_xlabel("PCA score")

    axes[0].set_ylabel("LDA score")
    axes[0].legend()

    fig.suptitle("PCA vs LDA — same scale for all classes", fontsize=14)
    plt.tight_layout()
    plt.show()

import matplotlib.pyplot as plt

def plot_recall_ablation(df, class_labels):
    plt.figure()

    for cls in class_labels:
        plt.plot(
            df["n_features"],
            df[f"recall_class_{cls}"],
            marker="o",
            label=f"class {cls}"
        )

    plt.plot(
        df["n_features"],
        df["recall_macro"],
        linestyle="--",
        color="black",
        label="macro"
    )

    plt.gca().invert_xaxis()
    plt.xlabel("Antal features")
    plt.ylabel("Recall")
    plt.title("Ablation validation (per klasse)")
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_lda_2d(X_lda, y, class_labels):
    """
    Plot 2D LDA projection of data points.
    
    Parameters:
    - X_lda: Transformed data in 2D LDA space (n_samples, 2)
    - y: Class labels (n_samples,)
    - class_labels: Unique class labels for legend
    """
    plt.figure(figsize=(8, 6))
    
    for cls in class_labels:
        mask = y == cls
        plt.scatter(
            X_lda[mask, 0],
            X_lda[mask, 1],
            label=f"Class {cls}",
            alpha=0.6,
            s=50
        )
    
    plt.xlabel("LD1 (1st Discriminant)")
    plt.ylabel("LD2 (2nd Discriminant)")
    plt.title("LDA 2D Projection")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

def plot_pca_2d(X_pca, y, class_labels, explained_var):
    """
    Plot 2D PCA projection of data points.
    
    Parameters:
    - X_pca: Transformed data in 2D PCA space (n_samples, 2)
    - y: Class labels (n_samples,)
    - class_labels: Unique class labels for legend
    - explained_var: Explained variance ratio for PC1 and PC2
    """
    plt.figure(figsize=(8, 6))
    
    for cls in class_labels:
        mask = y == cls
        plt.scatter(
            X_pca[mask, 0],
            X_pca[mask, 1],
            label=f"Class {cls}",
            alpha=0.6,
            s=50
        )
    
    plt.xlabel(f"PC1 ({explained_var[0]*100:.1f}% variance)")
    plt.ylabel(f"PC2 ({explained_var[1]*100:.1f}% variance)")
    plt.title("PCA 2D Projection")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
