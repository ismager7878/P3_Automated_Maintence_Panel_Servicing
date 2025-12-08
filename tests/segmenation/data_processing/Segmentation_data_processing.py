import os
from Panel import Panel
import csv
import numpy as np 


# take data from csv file
test = "segmentation_accuracy_log.csv"

# change for every test  # name plot data
test_name = "normal_test2"

data = []
Panels = []

csv_filename = f'tests/segmenation/raw_data/{test}'

# conver use csv to panel object
with open(csv_filename, mode='r') as file:
    csv_reader = csv.DictReader(file)
    for x, row in enumerate(csv_reader):
        data.append(row)

for i in range(len(data)):
    panel = Panel(data[i]["Filename"], data[i]["bottomtype"], data[i]["Groundtruth_boundingbox"], data[i]["Detected_boundingbox"])
    Panels.append(panel)

# get pose data from iou_score
list_differ_types = []
type_none =  False
for score in Panels[0].iou_score:
    list_differ_types.append(score.type)
    if score.type == "none":
        type_none = True

if type_none:
    list_differ_types.append("none")


# makes a list to save iou for each type
save_iou_for_type = [[] for _ in range(len(list_differ_types))]


panel_avarag_iou = []

for panel in Panels:
    
    panel_avarag_iou.append(panel.average_iou())    
    # save iou for each type
    for i, type in enumerate(list_differ_types):
        panel.specific_iou(type)
        save_iou_for_type[i] = save_iou_for_type[i] + panel.specific_iou(type)



# paner iou scores 
print("start recall precsion calculation")
data_name = "Panels_IOU_scores"
output_dir = f"tests/segmenation/processed_data/{test_name}/data_to_plot/Threshold"
os.makedirs(output_dir, exist_ok=True)  # Opret mappe hvis den ikke findes
output_dir += f"/{data_name}.csv"
with open(output_dir, mode='w', newline='') as file:
    csv_writer = csv.writer(file)
    csv_writer.writerow(["Threshold", "Precision", "Recall"])
    for i in range(100):
        i = (i+1) / 100
        tp = 0
        fp = 0
        fn = 0
        fnk = 0
        for Panel in Panels:
            for bt in Panel.iou_score:
                if "none" == bt.type:
                    fp += 1
                elif bt.iou == 0 and bt.type != "none":
                    fn += 1
                elif bt.iou > i:
                    tp += 1
                else:
                    fp += 1
        print("----------------------")
        print(f"fp: {fp}, tp: {tp}, fn: {fn}, fnk: {fnk}")
        precsion = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        print("-----------------------")
        print("    ")
        csv_writer.writerow([str(i), str(precsion), str(recall)])

print(f"\n✅ Panel IOU scores saved to: {output_dir}")

# genral iou scores for each type
def make_csv(type_name):
    output_dir = f"tests/segmenation/processed_data/{test_name}/data_to_plot"
    os.makedirs(output_dir, exist_ok=True)  # Opret mappe hvis den ikke findes
    output_dir += f"/{type_name}.csv"    


    with open(output_dir, mode='w', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow([type_name, "IOU"])
        for i, Panel in enumerate(Panels):
           for bt in Panel.iou_score:
               if type_name in bt.type:
                   csv_writer.writerow([bt.type, str(bt.iou)])




# Generate CSVs for each type
make_csv("selector_switch")
make_csv("main_switch")
make_csv("plug")
make_csv("circuit_breaker")


# Generate plots
from plotes import DataPlotter

data_dir = f"tests/segmenation/processed_data/{test_name}/data_to_plot"
plotter = DataPlotter(panels=Panels, data_dir=data_dir)
plotter.plot_all()

print(f"\n✅ Plots saved to: {plotter.base_path}")


from thresholdPlotter import ThresholdPlotter
csv_path = f"tests/segmenation/processed_data/{test_name}/data_to_plot/Threshold/{data_name}.csv"

# Lav threshold plots
threshold_plotter = ThresholdPlotter(csv_path=csv_path)
threshold_plotter.plot_all()
