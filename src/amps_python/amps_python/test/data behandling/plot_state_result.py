import matplotlib.pyplot as plt
import numpy as np
import json
from matplotlib import cm

with open("tests/Classification_test/Button_recognition_test/Report results/button_state_classification_results_implementation_test.json", 'r') as file1:
    json_data_imp = json.load(file1)

with open("tests/Classification_test/Button_recognition_test/Report results/button_state_classification_results_module.json", 'r') as file2:
    json_data_module = json.load(file2)

    

def plot_2x2(json_data, button_type):
    b_0 = json_data[button_type]["confusion_matrix"][0]
    b_1 = json_data[button_type]["confusion_matrix"][1]

    cm1 = np.array([
        [b_0[0], b_0[1]],
        [b_1[0],   b_1[1]]
    ])

    classes = ["On", "Off"]

    # Normalize rows into %
    row_sums = cm1.sum(axis=1, keepdims=True)
    # Avoid division by zero: replace 0 with 1 (rows with no samples will stay 0)
    row_sums = np.where(row_sums == 0, 1, row_sums)
    cm_norm = (cm1/ row_sums) * 100

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


def plot_3x3(json_data, button_type):
    b_0 = json_data[button_type]["confusion_matrix"][0]
    b_1 = json_data[button_type]["confusion_matrix"][1]
    b_2 = json_data[button_type]["confusion_matrix"][2]

    cm1 = np.array([
        [b_0[0], b_0[1], b_0[2]],
        [b_1[0], b_1[1], b_1[2]],
        [b_2[0], b_2[1], b_2[2]]
    ])

    classes = ["0", "1", "2"]

    # Normalize rows into %
    row_sums = cm1.sum(axis=1, keepdims=True)
    # Avoid division by zero: replace 0 with 1 (rows with no samples will stay 0)
    row_sums = np.where(row_sums == 0, 1, row_sums)
    cm_norm = (cm1/ row_sums) * 100

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

def calculate_precision_recall(json_data, button_type):
    confusion_matrix = json_data[button_type]["confusion_matrix"]
    
    if len(confusion_matrix) == 2:
        # For 2x2 confusion matrix
        true_positive = confusion_matrix[0][0] + confusion_matrix[1][1]
        false_positive = confusion_matrix[0][1] + confusion_matrix[1][0]
        false_negative = json_data[button_type]["false_negatives"]
        
    elif len(confusion_matrix) == 3:
        # For 3x3 confusion matrix
        true_positive = confusion_matrix[0][0] + confusion_matrix[1][1] + confusion_matrix[2][2]
        false_positive = (confusion_matrix[0][1] + confusion_matrix[0][2] + 
                         confusion_matrix[1][0] + confusion_matrix[1][2] + 
                         confusion_matrix[2][0] + confusion_matrix[2][1])
        false_negative = json_data[button_type]["false_negatives"]
    
    # Calculate precision and recall
    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
    
    return precision, recall

def visualize_pr_separate_subplots(json_data, goal_file_name):
    """Visualiser precision og recall i to subplots side om side"""
    
    plt.rcParams.update({'font.size': 18})
    
    # Beregn precision og recall for hver knaptype
    button_types = ['circuit_breaker', 'selector_switch', 'main_switch']
    display_names = ['Circuit breaker switch', 'Rotary control switch', 'Rotary power switch']
    
    precision = []
    recall = []
    
    for btn_type in button_types:
        p, r = calculate_precision_recall(json_data, btn_type)
        precision.append(p)
        recall.append(r)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    
    x = np.arange(len(display_names))
    width = 0.6
    
    # Precision subplot
    bars1 = ax1.bar(x, precision, width, color='#ff7f0e', edgecolor='black', alpha=0.6)
    ax1.set_xlabel('Switch Types', fontsize=20, fontweight='bold')
    ax1.set_ylabel('Score (%)', fontsize=20, fontweight='bold')
    ax1.set_title('Precision per Switch Type', fontsize=22, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(display_names, fontsize=18)
    ax1.set_ylim(0, 1.05)
    
    # Format y-axis as percentage
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y*100:.0f}%'))
    
    ax1.grid(True, alpha=0.2, axis='y')
    
    # Tilføj reference linjer MED labels (opdateret tekst)
    ax1.axhline(y=0.9, color='red', linestyle='--', alpha=0.75, linewidth=2, label='Preferred (90%)')
    ax1.axhline(y=0.8, color='black', linestyle='--', alpha=0.75, linewidth=2, label='Marginal (80%)')
    
    # Tilføj værdier på precision bars (nu i procent)
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height*100:.1f}%', ha='center', va='bottom', fontsize=16, fontweight='bold')
    
    # Tilføj legend til precision plot
    ax1.legend(fontsize=14, loc='lower right', framealpha=0.9)
    
    # Recall subplot
    bars2 = ax2.bar(x, recall, width, color='#1f77b4', edgecolor='black', alpha=0.6)
    ax2.set_xlabel('Switch Types', fontsize=20, fontweight='bold')
    ax2.set_ylabel('Score (%)', fontsize=20, fontweight='bold')
    ax2.set_title('Recall per Switch Type', fontsize=22, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(display_names, fontsize=18)
    ax2.set_ylim(0, 1.05)
    
    # Format y-axis as percentage
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y*100:.0f}%'))
    
    ax2.grid(True, alpha=0.2, axis='y')
    
    # Tilføj reference linjer MED labels (opdateret tekst)
    ax2.axhline(y=0.75, color='red', linestyle='--', alpha=0.75, linewidth=2, label='Preferred (75%)')
    ax2.axhline(y=0.65, color='black', linestyle='--', alpha=0.75, linewidth=2, label='Marginal (65%)')
    
    # Tilføj værdier på recall bars (nu i procent)
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height*100:.1f}%', ha='center', va='bottom', fontsize=16, fontweight='bold')
    
    # Tilføj legend til recall plot
    ax2.legend(fontsize=14, loc='lower right', framealpha=0.9)
    
    # Overordnet titel
    #fig.suptitle('Model Performance: Precision vs Recall', fontsize=24, fontweight='bold', y=1.02)
    
    # Juster layout (øg top margin for at give plads til suptitle)
    plt.tight_layout(rect=[0, 0, 1, 0.96])  # [left, bottom, right, top]
    #plt.show()
    plt.savefig(goal_file_name)

# Calculate precision and recall (for reference)
#precission_breaker, recall_breaker = calculate_precision_recall(json_data, "circuit_breaker")
#precission_rotary, recall_rotary = calculate_precision_recall(json_data, "selector_switch")
#precission_main, recall_main = calculate_precision_recall(json_data, "main_switch")

# Plot confusion matrices
#plot_2x2(json_data, "circuit_breaker")
#plot_3x3(json_data, "selector_switch")
#plot_2x2(json_data, "main_switch")

# Plot the new precision-recall visualization
visualize_pr_separate_subplots(json_data_imp, "/home/petur/Pictures/Raport_billeder/state_imp1_test.jpg")
visualize_pr_separate_subplots(json_data_module, "/home/petur/Pictures/Raport_billeder/state_module1_test.jpg")