import os
import json

IOU_THRESHOLD = 0.35

TYPE_DICTIONARY = {
    "circuit_breaker": 1,
    "selector_switch": 2,
    "main_switch": 3
}

def convertGroundData(ground_data):
    new_ground_data = []

    circuit_breakers = ground_data["circuit_breaker"]

    selector_switches = ground_data["selector_switch"]

    main_switches = ground_data["main_switch"]

    for button in circuit_breakers:
        if len(button["states"]) < 1:
            new_ground_data.append(button)
            continue

        states = button["states"]

        states.reverse()

        block_y_range = button["transformed_pos_xy"][1] - button["transformed_pos_xy"][3]
        state_height = block_y_range / len(button["states"])
        for i, state in enumerate(button["states"]):
            new_button = {
                "transformed_pos_xy": [
                    button["transformed_pos_xy"][0],
                    int(button["transformed_pos_xy"][1] - i * state_height),
                    button["transformed_pos_xy"][2],
                    int(button["transformed_pos_xy"][1] - (i + 1) * state_height)
                ],
                "state": state,
                "type": "circuit_breaker"
            }
            new_ground_data.append(new_button)
    
    for button in selector_switches:
        new_button = {
            "transformed_pos_xy": button["transformed_pos_xy"],
            "state": button["states"][0],
            "type": "selector_switch"
        }
        new_ground_data.append(new_button)

    for button in main_switches:
        new_button = {
            "transformed_pos_xy": button["transformed_pos_xy"],
            "state": button["states"][0],
            "type": "main_switch"
        }
        new_ground_data.append(new_button)
    
    return new_ground_data

def match_button_types(state_data, ground_data_buttons):

    matched_buttons = []

    for i, state_button in enumerate(state_data):

        if(state_button["state"] == ""):
            continue  # Skip no state buttons

        allIoUs = []
        
        #Check against all ground buttons
        for ground_button in ground_data_buttons:
            iou = calculate_iou(state_button["bounding_box"], ground_button["transformed_pos_xy"])
            allIoUs.append({
                "iou": iou,
                "ground_button": ground_button
            })

        #Find the max IoU entry --- Best Match
        max_iou_entry = max(allIoUs, key=lambda x: x["iou"])

        #Check if the max IoU is above the threshold and save the match
        if max_iou_entry["iou"] >= IOU_THRESHOLD:
            matched_buttons.append({
                "iou": max_iou_entry["iou"],
                "state_button": state_button,
                "ground_button": max_iou_entry["ground_button"] 
            })
    
    for match in matched_buttons:
        dublicates = []

        for button in matched_buttons:
            if match['state_button'] == button['state_button']:
                continue  # Skip self-comparison
            if match['ground_button'] == button['ground_button']:
                dublicates.append(button)
        
        if len(dublicates) > 0:
            dublicates.sort(key=lambda x: x['iou'], reverse=True)
            for i, dub in enumerate(dublicates):
                if(i == 0):
                    continue  # Keep the best match
                matched_buttons.remove(dub)
    
    return matched_buttons

def calculate_iou(boxA, boxB):
    # Beregn koordinaterne for krydsningsområdet
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    # Beregn arealet af krydsningsområdet
    interArea = max(0, xB - xA) * max(0, yB - yA)

    # Beregn arealet af begge bokse
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    # Beregn IoU
    iou = interArea / float(boxAArea + boxBArea - interArea)

    return iou

def find_valid_classifications(ground_data, state_data, ground_file, state_file):

    validClassification = []
    
    # Find the matches between type_data and ground_data based on IoU
    matched_buttons = match_button_types(state_data, ground_data)

    for match in matched_buttons:
        state_button = match["state_button"]
        ground_button = match["ground_button"]

        if state_button["type"] == TYPE_DICTIONARY[ground_button["type"]]:
            validClassification.append({
                "state_button": state_button,
                "ground_button": ground_button,
                "iou": match["iou"]
            })
        
    return validClassification

def calculate_metrics(valid_classifications):
    trues = 0
    falses = 0
    
    for classification in valid_classifications:
        if classification["ground_button"]["state"] == classification["state_button"]["state"]:
            trues += 1
        else:
            print("Wrong Button State:")
            print(f"State Button: {classification['state_button']}, \n Ground Button: {classification['ground_button']}")
            falses += 1

    if trues + falses == 0:
        return 0
        
    return (trues/(trues+falses)) 
    
    
    

        



def main():
    root_ground = "tests/Classification_test/Button_recognition_test/Ground_truth/truth:"
    root_state_class  = "tests/Classification_test/Button_recognition_test/button_data/data:"

    # Collect groundtruth files
    ground_filer = []
    for dirpath, dirnames, filenames in os.walk(root_ground):
        for fil in filenames:
            ground_filer.append(os.path.join(dirpath, fil))

    state_filer = []
    for dirpath, dirnames, filenames in os.walk(root_state_class):
        for fil in filenames:
            state_filer.append(os.path.join(dirpath, fil))

    ground_filer.sort()
    state_filer.sort()

    corr_pers = []

    for ground_file, state_file in zip(ground_filer, state_filer):
        with open(ground_file, 'r') as f:
            ground_data = json.load(f)

        with open(state_file, 'r') as f:
            state_data = json.load(f)

        print(f"on Image: {ground_data["image_filename"]}")

        ground_data = convertGroundData(ground_data)
        
        valid_classifications = find_valid_classifications(ground_data, state_data, ground_file, state_file)

        # print(f"Processed files: {ground_file} and {state_file}")
        # print("-----")
        # print("")
        # print("Found valid classifications:")
        # for classification in valid_classifications:
        #     print(f"State Button: {classification['state_button']}, \n Ground Button: {classification['ground_button']}, \n IoU: {classification['iou']}")
        # print("")
        # print("====================================")

        # if len(valid_classifications) == 0:
        #     print("No valid classifications found in these files.")
        #     print("====================================")
        
        corr_per = calculate_metrics(valid_classifications)
        corr_pers.append(corr_per)
        print(f"Correct classification percentage: {corr_per*100:.2f}%")
        print("")
        
    
    overall_accuracy = sum(corr_pers) / len(corr_pers) if len(corr_pers) > 0 else 0
    print(f"Overall Correct classification percentage across all files: {overall_accuracy*100:.2f}%")
            


if __name__ == "__main__":
    main()