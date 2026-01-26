import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

def run_pca(X, feature_names, n_components=None):
    """
    Runs PCA and returns interpretable results.
    NO plotting.
    """
    X_scaled = StandardScaler().fit_transform(X)

    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_scaled)

    results = {
        "explained_variance_ratio": pca.explained_variance_ratio_,
        "components": pca.components_,  # shape: (n_components, n_features)
        "feature_names": feature_names,
        "singular_values": pca.singular_values_,
    }

    return X_pca, results