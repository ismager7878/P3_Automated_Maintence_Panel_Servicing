import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import recall_score

def ablation_per_class_recall(
    X,
    y,
    feature_order,
    class_labels,
    min_features=1,
    cv_splits=5,
    random_state=42
):
    """
    Feature ablation med cross-validation.
    Returnerer recall pr. klasse for hvert ablation-trin.
    """

    results = []

    cv = StratifiedKFold(
        n_splits=cv_splits,
        shuffle=True,
        random_state=random_state
    )

    for k in range(len(feature_order) - min_features + 1):
        keep_idx = feature_order[k:]
        X_sub = X[:, keep_idx]

        recalls = {cls: [] for cls in class_labels}

        for train_idx, test_idx in cv.split(X_sub, y):
            pipe = Pipeline([
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=1000))
            ])

            pipe.fit(X_sub[train_idx], y[train_idx])
            y_pred = pipe.predict(X_sub[test_idx])

            per_class = recall_score(
                y[test_idx],
                y_pred,
                labels=class_labels,
                average=None,
                zero_division=0
            )

            for cls, r in zip(class_labels, per_class):
                recalls[cls].append(r)

        result = {
            "n_features": X_sub.shape[1],
            "kept_features": keep_idx
        }

        for cls in class_labels:
            result[f"recall_class_{cls}"] = np.mean(recalls[cls])

        result["recall_macro"] = np.mean(
            [result[f"recall_class_{cls}"] for cls in class_labels]
        )

        results.append(result)

    return results
