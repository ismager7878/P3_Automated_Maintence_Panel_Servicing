import matplotlib.pyplot as plt
import numpy as np
import json

def visualize_pr_separate_subplots(json_data, goal_file_name):
    """Visualiser precision og recall i to subplots side om side"""
    
    plt.rcParams.update({'font.size': 18})
    
    classes = ['Circuit breaker switch', 'Rotary control switch', 'Rotary power switch']
    precision = [
        json_data["breaker"]["precision"],
        json_data["rotary"]["precision"],
        json_data["main"]["precision"]
    ]
    recall = [
        json_data["breaker"]["recall"],
        json_data["rotary"]["recall"],
        json_data["main"]["recall"]
    ]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    
    x = np.arange(len(classes))
    width = 0.6
    
    # Precision subplot
    bars1 = ax1.bar(x, precision, width, color='#ff7f0e', edgecolor='black', alpha=0.6)
    ax1.set_xlabel('Switch Types', fontsize=20, fontweight='bold')
    ax1.set_ylabel('Score (%)', fontsize=20, fontweight='bold')  # Ændret til %
    ax1.set_title('Precision per Switch Type', fontsize=22, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(classes, fontsize=18)
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
    bars2 = ax2.bar(x, recall, width, color="#1f77b4", edgecolor='black', alpha=0.6)
    ax2.set_xlabel('Switch Types', fontsize=20, fontweight='bold')
    ax2.set_ylabel('Score (%)', fontsize=20, fontweight='bold')  # Ændret til %
    ax2.set_title('Recall per Switch Type', fontsize=22, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(classes, fontsize=18)
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
    plt.tight_layout()  # [left, bottom, right, top]rect=[0, 0, 1, 0.96]
    #plt.show()
    plt.savefig(goal_file_name)



with open("tests/Classification_test/Button_recognition_test/results/All_data/confusion_matrix_implementation_test.json", 'r') as file1:
    json_imp = json.load(file1)
# Brug:
with open("tests/Classification_test/Button_recognition_test/results/All_data/confusion_matrix_module.json", "r") as file2:
    json_module = json.load(file2)

visualize_pr_separate_subplots(json_imp, "/home/petur/Pictures/Raport_billeder/classi_imp1_test.jpg")
visualize_pr_separate_subplots(json_module, "/home/petur/Pictures/Raport_billeder/classi_module1_test.jpg")