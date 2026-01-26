import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.preprocessing import StandardScaler

def run_lda(X, y, feature_names, n_components=None):
    X_scaled = StandardScaler().fit_transform(X)

    lda = LinearDiscriminantAnalysis(n_components=n_components)
    lda.fit(X_scaled, y)

    # coef_ shape: (n_classes, n_features) for multiclass OvR
    # Each row shows feature weights for discriminating that class
    coef = lda.coef_
    
    # Per-class discriminative power: absolute coefficient values
    per_class_lda_score = np.abs(coef)  # (n_classes, n_features)
    
    # Mean discriminative power across all classes
    mean_lda_score = per_class_lda_score.mean(axis=0)

    results = {
        "coef": coef,
        "scalings": lda.scalings_,
        "per_class_lda_score": per_class_lda_score,  # (n_classes, n_features)
        "mean_lda_score": mean_lda_score,
        "class_labels": lda.classes_,
        "feature_names": feature_names,
    }

    return lda.transform(X_scaled), results
