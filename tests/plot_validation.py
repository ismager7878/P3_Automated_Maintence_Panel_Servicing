import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import ast

# Read the CSV file
csv_path = 'Classification_test/Button_recognition_test/results/recall_results.csv'
df = pd.read_csv(csv_path)

# Feature names reference (indices 0-15 + hist bins)
feature_names = [
    'std_depth',      # 0
    'std_intensity',  # 1
    'min_hue',        # 2
    'max_hue',        # 3
    'area',           # 4
    'HW_ratio',       # 5
    'min_value',      # 6
    'max_value',      # 7
    'hue_bin1',      # 8
    'hue_bin2',      # 9
    'hue_bin3',      # 10
    'hue_bin4',      # 11
    'hue_bin5',      # 12
    'hue_bin6',      # 13
    'hue_bin7',      # 14
    'hue_bin8'        # 15
]

# Parse exclusions column
def parse_exclusions(excl_str):
    if excl_str == '[]':
        return []
    try:
        return ast.literal_eval(excl_str)
    except:
        return []

df['exclusions_parsed'] = df['exclusions'].apply(parse_exclusions)
df['num_exclusions'] = df['exclusions_parsed'].apply(len)

# Get the exclusion order from the data
# Find a row with maximum exclusions to get the full order
max_excl_idx = df['num_exclusions'].idxmax()
full_exclusion_order = df.loc[max_excl_idx, 'exclusions_parsed']

# Calculate average recall for each class at each exclusion amount
classes = ['BREAKER', 'THREE_STATE_SWITCH', 'EMERGENCY_STOP']
exclusion_amounts = sorted(df['num_exclusions'].unique())

results = {cls: [] for cls in classes}

for num_excl in exclusion_amounts:
    subset = df[df['num_exclusions'] == num_excl]
    for cls in classes:
        avg_recall = subset[cls].mean()
        results[cls].append(avg_recall)

# Create the plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), gridspec_kw={'width_ratios': [3, 1]})

# Plot the recall curves
for cls in classes:
    ax1.plot(exclusion_amounts, results[cls], marker='o', linewidth=2, markersize=8, label=cls)

ax1.set_xlabel('Number of Features Excluded', fontsize=12)
ax1.set_ylabel('Average Recall', fontsize=12)
ax1.set_title('Average Recall vs Feature Exclusion', fontsize=14, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.set_ylim([0, 1.05])

# Add text box showing feature exclusion order
exclusion_order_text = "Feature Exclusion Order:\n" + "="*30 + "\n"
for i, feat_idx in enumerate(full_exclusion_order):
    exclusion_order_text += f"{i+1:2d}. {feature_names[feat_idx]:<20} (idx: {feat_idx})\n"

ax2.text(0.05, 0.95, exclusion_order_text, 
         transform=ax2.transAxes,
         fontsize=9,
         verticalalignment='top',
         fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

ax2.axis('off')

plt.tight_layout()
plt.savefig('Classification_test/Button_recognition_test/results/recall_vs_exclusions.png', 
            dpi=300, bbox_inches='tight')
plt.show()

print(f"\nPlot saved to: Classification_test/Button_recognition_test/results/recall_vs_exclusions.png")
print(f"\nSummary Statistics:")
print("="*60)
for cls in classes:
    print(f"\n{cls}:")
    print(f"  Initial recall (0 exclusions):  {results[cls][0]:.4f}")
    print(f"  Final recall ({len(full_exclusion_order)} exclusions): {results[cls][-1]:.4f}")
    print(f"  Change: {results[cls][-1] - results[cls][0]:.4f}")
