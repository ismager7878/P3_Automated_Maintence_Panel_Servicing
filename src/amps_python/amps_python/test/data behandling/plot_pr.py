import matplotlib.pyplot as plt
import numpy as np
import json

def extract_pr_from_json(json_data):
    """
    Ekstraher precision og recall fra JSON data, uanset format.
    Returnerer dictionaries med precision og recall for hver klasse.
    """
    precision = {}
    recall = {}
    
    # Check hvilket format der er brugt
    keys = list(json_data.keys())
    
    # Format 1: breaker, rotary, main keys (type classification)
    if 'breaker' in keys and 'rotary' in keys and 'main' in keys:
        classes_mapping = {
            'breaker': 'Circuit breaker switch',
            'rotary': 'Rotary control switch', 
            'main': 'Rotary power switch'
        }
        
        for key, display_name in classes_mapping.items():
            if key in json_data:
                precision[display_name] = json_data[key]['precision']
                recall[display_name] = json_data[key]['recall']
    
    # Format 2: circuit_breaker, main_switch, selector_switch keys (state classification)
    elif 'circuit_breaker' in keys or 'main_switch' in keys or 'selector_switch' in keys:
        classes_mapping = {
            'circuit_breaker': 'Circuit breaker switch',
            'main_switch': 'Rotary power switch',
            'selector_switch': 'Rotary control switch'
        }
        
        for key, display_name in classes_mapping.items():
            if key in json_data:
                # Bemærk: i dette format hedder felterne precision_avg og recall_avg
                precision[display_name] = json_data[key]['precision_avg']
                recall[display_name] = json_data[key]['recall_avg']
    
    else:
        # Hvis intet match, prøv at finde alle nøgler der indeholder precision/recall
        for key, value in json_data.items():
            if isinstance(value, dict):
                if 'precision' in value or 'precision_avg' in value:
                    display_name = key.replace('_', ' ').title()
                    precision[display_name] = value.get('precision', value.get('precision_avg', 0))
                    recall[display_name] = value.get('recall', value.get('recall_avg', 0))
    
    return precision, recall

def visualize_pr_separate_subplots(json_data, goal_file_name=None):
    """Visualiser precision og recall i to subplots side om side"""
    
    plt.rcParams.update({'font.size': 18})
    
    # Ekstraher data fra JSON - bruger den nye funktion
    precision_dict, recall_dict = extract_pr_from_json(json_data)
    
    # Sorter klasser for konsistent visning
    classes = sorted(precision_dict.keys())
    precision = [precision_dict[cls] for cls in classes]
    recall = [recall_dict[cls] for cls in classes]
    
    # Check om det er state classification (format 2) og juster titler
    is_state_classification = 'circuit_breaker' in json_data or 'main_switch' in json_data or 'selector_switch' in json_data
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    
    x = np.arange(len(classes))
    width = 0.6
    
    # Bestem titler baseret på type
    if is_state_classification:
        precision_title = 'State Precision per Switch Type'
        recall_title = 'State Recall per Switch Type'
    else:
        precision_title = 'Type Precision per Switch Type'
        recall_title = 'Type Recall per Switch Type'
    
    # Precision subplot
    bars1 = ax1.bar(x, precision, width, color='#ff7f0e', edgecolor='black', alpha=0.6)
    ax1.set_xlabel('Switch Types', fontsize=20, fontweight='bold')
    ax1.set_ylabel('Score (%)', fontsize=20, fontweight='bold')
    ax1.set_title(precision_title, fontsize=22, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(classes, fontsize=18)
    ax1.set_ylim(0, 1.05)
    
    # Format y-axis as percentage
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y*100:.0f}%'))
    
    ax1.grid(True, alpha=0.2, axis='y')
    
    # Tilføj reference linjer MED labels
    ax1.axhline(y=0.9, color='red', linestyle='--', alpha=0.75, linewidth=2, label='Preferred (90%)')
    ax1.axhline(y=0.8, color='black', linestyle='--', alpha=0.75, linewidth=2, label='Marginal (80%)')
    
    # Tilføj værdier på precision bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height*100:.1f}%', ha='center', va='bottom', fontsize=16, fontweight='bold')
    
    # Tilføj legend til precision plot
    ax1.legend(fontsize=14, loc='lower right', framealpha=0.9)
    
    # Recall subplot
    bars2 = ax2.bar(x, recall, width, color="#1f77b4", edgecolor='black', alpha=0.6)
    ax2.set_xlabel('Switch Types', fontsize=20, fontweight='bold')
    ax2.set_ylabel('Score (%)', fontsize=20, fontweight='bold')
    ax2.set_title(recall_title, fontsize=22, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(classes, fontsize=18)
    ax2.set_ylim(0, 1.05)
    
    # Format y-axis as percentage
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y*100:.0f}%'))
    
    ax2.grid(True, alpha=0.2, axis='y')
    
    # Tilføj reference linjer MED labels
    ax2.axhline(y=0.75, color='red', linestyle='--', alpha=0.75, linewidth=2, label='Preferred (75%)')
    ax2.axhline(y=0.65, color='black', linestyle='--', alpha=0.75, linewidth=2, label='Marginal (65%)')
    
    # Tilføj værdier på recall bars
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height*100:.1f}%', ha='center', va='bottom', fontsize=16, fontweight='bold')
    
    # Tilføj legend til recall plot
    ax2.legend(fontsize=14, loc='lower right', framealpha=0.9)
    
    # Juster layout
    plt.tight_layout()
    
    if goal_file_name:
        plt.savefig(goal_file_name, dpi=300, bbox_inches='tight')
    plt.show()

with open("tests/Classification_test/Button_recognition_test/Report results/All_data/confusion_matrix_implementation_test.json", 'r') as file1:
    type_imp = json.load(file1)

with open("tests/Classification_test/Button_recognition_test/Report results/All_data/confusion_matrix_module.json", "r") as file2:
    type_module = json.load(file2)

with open("tests/Classification_test/Button_recognition_test/Report results/button_state_classification_results_implementation_test.json", "r") as file3:
    state_imp = json.load(file3)

with open("tests/Classification_test/Button_recognition_test/Report results/button_state_classification_results_module.json", "r") as file4:
    state_module = json.load(file4)

# Brug funktionen med dine data
visualize_pr_separate_subplots(type_imp, "/home/petur/Pictures/Raport_billeder/type_imp.jpg")
visualize_pr_separate_subplots(type_module, "/home/petur/Pictures/Raport_billeder/type_module.jpg")
visualize_pr_separate_subplots(state_imp, "/home/petur/Pictures/Raport_billeder/state_imp.jpg")
visualize_pr_separate_subplots(state_module, "/home/petur/Pictures/Raport_billeder/state_module.jpg")