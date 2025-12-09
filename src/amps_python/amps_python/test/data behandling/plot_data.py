import matplotlib.pyplot as plt
import numpy as np
import json
from matplotlib import cm

def grab_ground_truth():
    with open("tests/Classification_test/Button_recognition_test/results/All_data/confusion matrix 2", 'r') as file:
        data = json.load(file)

    breaker = data["confusion_score"]["breaker_score"]
    rotary = data["confusion_score"]["rotary_score"]
    main = data["confusion_score"]["main_score"]
    plug = data["confusion_score"]["plug_score"]

    return breaker, rotary, main, plug

breaker, rotary, main, plug = grab_ground_truth()


cm1 = np.array([
    [breaker[0], breaker[1], breaker[2]],
    [rotary[1],   rotary[0], rotary[2]],
    [main[1],   main[2],  main[0]]
])

classes = ["Breaker", "Rotary", "Main"]

# Normalize rows into %
row_sums = cm1.sum(axis=1, keepdims=True)
# Avoid division by zero: replace 0 with 1 (rows with no samples will stay 0)
row_sums = np.where(row_sums == 0, 1, row_sums)
cm_norm = (cm1 / row_sums) * 100

fig, ax = plt.subplots(figsize=(8, 7))

# Choose colormap
#cmap = cm.get_cmap("cividis")
cmap = cm.get_cmap("Greens")
im = ax.imshow(cm_norm, cmap=cmap)

ax.set_xticks(np.arange(len(classes)))
ax.set_yticks(np.arange(len(classes)))
ax.set_xticklabels(classes, fontsize=12)
ax.set_yticklabels(classes, fontsize=12)
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

# Add text with automatic black/white contrast
for i in range(cm_norm.shape[0]):
    for j in range(cm_norm.shape[1]):
        value = cm_norm[i, j]

        # Normalize value to 0-1 for colormap lookup
        norm_val = (value - cm_norm.min()) / (cm_norm.max() - cm_norm.min())
        r, g, b, _ = cmap(norm_val)

        # Compute luminance (human perception)
        luminance = 0.299*r + 0.587*g + 0.114*b

        # Choose text color based on luminance threshold
        text_color = "black" if luminance > 0.5 else "white"

        ax.text(j, i, f"{value:.1f}%",
                ha="center", va="center",
                fontsize=14, fontweight="bold",
                color=text_color)

ax.set_xlabel("Ground truth", fontsize=14)
ax.set_ylabel("Predicted", fontsize=14)
ax.set_title("Normalized Confusion Matrix (%)", fontsize=16)

plt.tight_layout()
plt.show()
