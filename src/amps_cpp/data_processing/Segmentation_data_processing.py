from Panel import Panel
import csv
import numpy as np 

data = []
Panels = []
test = "segmentation_accuracy_log.csv"
csv_filename = f'tests/segmenation/{test}'
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
save_iou_for_type = [0]*len(list_differ_types)
for panel in Panels:
    
    if (panel.filename == "datasets/auto_aligned_dataset/button_pose2/img3_0"):
        print(f"{panel.filename} show filer her---------------------------------")
        for bt in panel.iou_score:
            bt.show()
        print("-----")

    
    print("filename: ")
    print(panel.filename)
    for i, type in enumerate(list_differ_types):
        panel.specific_iou(type)
        save_iou_for_type[i] = save_iou_for_type[i] + panel.specific_iou(type)

for i, type in enumerate(list_differ_types):
    avg_iou = save_iou_for_type[i] / len(Panels)
    print(f"Average IOU for type '{type}': {avg_iou}")


    
