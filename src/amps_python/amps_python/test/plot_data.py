import matplotlib.pyplot as plt
import numpy as np
import json

def grab_ground_truth():
    with open("tests/Classification_test/Button_recognition_test/results/All_data/confusion matrix", 'r') as file:
        data = json.load(file)

    breaker = data["confusion_score"]["breaker_score"]
    rotary = data["confusion_score"]["rotary_score"]
    main = data["confusion_score"]["main_score"]
    plug = data["confusion_score"]["plug_score"]

    return breaker, rotary, main, plug

breaker, rotary, main, plug = grab_ground_truth()

cm1 = np.array([
    [breaker[0], breaker[1], breaker[2], breaker[3]],
    [rotary[1],   rotary[0], rotary[2],   rotary[3]],
    [main[1],   main[2],  main[0],   main[3]],
    [plug[1], plug[2], plug[3],  plug[0]],
])

# Confusion matrix (antal)
cm = np.array([
    [423, 4,   2,   1],
    [2,   58, 17,   0],
    [8,   0,  38,   0],
    [0, 100, 15,  59],
])

classes = ["breaker", "rotary", "main", "plug"]

# Normaliser hver række til %
row_sums = cm1.sum(axis=1, keepdims=True)
cm_norm = (cm1 / row_sums) * 100

fig, ax = plt.subplots(figsize=(8, 7))

# Plot matrixen
im = ax.imshow(cm_norm)

# Akse labels
ax.set_xticks(np.arange(len(classes)))
ax.set_yticks(np.arange(len(classes)))
ax.set_xticklabels(classes, fontsize=12)
ax.set_yticklabels(classes, fontsize=12)

plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

# Skriv procenter i boksene
for i in range(cm_norm.shape[0]):
    for j in range(cm_norm.shape[1]):
        ax.text(
            j, i, 
            f"{cm_norm[i, j]:.1f}%", 
            ha="center", va="center",
            fontsize=14, fontweight="bold"
        )

ax.set_xlabel("Ground truth", fontsize=14)
ax.set_ylabel("Predicted", fontsize=14)
ax.set_title("Normalized Confusion Matrix (%)", fontsize=16)

plt.tight_layout()
plt.show()
