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
with open(csv_filename, mode='r') as file:
    csv_reader = csv.DictReader(file)
    for x, row in enumerate(csv_reader):
        data.append(row)

for i in range(len(data)):
    panel = Panel(data[i]["Filename"], data[i]["bottomtype"], data[i]["Groundtruth_boundingbox"], data[i]["Detected_boundingbox"])
    Panels.append(panel)


types = Panels[0].list_types("plug")

print(types)

# get pose data from iou_score
list_differ_types = []
for score in Panels[0].iou_score:
    list_differ_types.append(score.type)

print(len(list_differ_types))

# makes a list to save iou for each type
save_iou_for_type = [[] for _ in range(len(list_differ_types))]


panel_avarag_iou = []

for panel in Panels:
    
    panel_avarag_iou.append(panel.average_iou())    
    # save iou for each type
    for i, type in enumerate(list_differ_types):
        panel.specific_iou(type)
        save_iou_for_type[i] = save_iou_for_type[i] + panel.specific_iou(type)




    



data_name = "Panel_IOU_scores"
output_dir = f"tests/segmenation/processed_data/{test_name}/data_to_plot"
os.makedirs(output_dir, exist_ok=True)  # Opret mappe hvis den ikke findes
output_dir += f"/{data_name}.csv"

with open(output_dir, mode='w', newline='') as file:
    csv_writer = csv.writer(file)
    csv_writer.writerow(["Panel_Filename", "Average_IOU"])
    for Panel in Panels:
        csv_writer.writerow([Panel.filename, str(Panel.average_iou())])


def make_csv(type_name):
    output_dir = f"tests/segmenation/processed_data/{test_name}/data_to_plot"
    os.makedirs(output_dir, exist_ok=True)  # Opret mappe hvis den ikke findes
    output_dir += f"/{type_name}.csv"    


    with open(output_dir, mode='w', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow([type_name, "IOU"])
        for i, Panel in enumerate(Panels):
           for bt in Panel.iou_score:
               bt.show()
               if type_name in bt.type:
                   csv_writer.writerow([bt.type, str(bt.iou)])


data_name = "selected_switch_types_IOU_scores"


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


list_threshold = [0.3, 0.5, 0.7, 0.8, 0.9]

threshold_name = []

for th in list_threshold:
    threshold_name.append(str(th))



def make_threshold_csv(threshold,data_dir):
    for sep in threshold:

        output_dir = f"tests/segmenation/processed_data/{test_name}/data_to_plot"
        os.makedirs(output_dir, exist_ok=True)  # Opret mappe hvis den ikke findes
        output_dir += f"/iou_threshold_{str(threshold)}.csv"    


        with open(output_dir, mode='w', newline='') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow([f"True Positives","False_Positives", 
                "False_Negatives"])
            
        