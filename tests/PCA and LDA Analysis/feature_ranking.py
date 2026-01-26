import numpy as np
import pandas as pd

def score_features(pca_results, lda_results, feature_types=None):
    feature_names = pca_results["feature_names"]

    # ---------- PCA SCORE (RAW) ----------
    # Weight each component by its explained variance ratio
    weighted_components = (
        np.abs(pca_results["components"]) * 
        pca_results["explained_variance_ratio"][:, np.newaxis]
    )
    pca_score = weighted_components.sum(axis=0)
    
    # No normalization - keep raw weighted PCA scores for comparison

    df = pd.DataFrame({
        "feature": feature_names,
        "pca_score": pca_score,
    })

    # ---------- LDA SCORE (RAW, PER KLASSE) ----------
    for i, cls in enumerate(lda_results["class_labels"]):
        df[f"lda_class_{cls}"] = lda_results["per_class_lda_score"][i]

    # No normalization - keep raw LDA coefficients for comparison
    lda_cols = [c for c in df.columns if c.startswith("lda_class_")]

    # Mean LDA (nu ærlig)
    df["lda_mean"] = df[lda_cols].mean(axis=1)

    # ---------- FEATURE TYPES ----------
    if feature_types is not None:
        df["feature_type"] = feature_types
    else:
        df["feature_type"] = "unknown"

    return df
