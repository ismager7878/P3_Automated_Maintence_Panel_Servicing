import os
import json

IOU_THRESHOLD = 0.35

TYPE_DICTIONARY = {
    "circuit_breaker": 1,
    "selector_switch": 2,
    "main_switch": 3
}

CIRCUIT_BREAKER_COUNT = 14
SELECTOR_COUNT = 5
MAIN_SWITCH_COUNT = 2


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
    breaker_matrix = [
        [0,0],
        [0,0]
    ]
    main_switch_matrix = [
        [0,0],
        [0,0]
    ]
    selector_matrix = [
        [0,0,0],
        [0,0,0],
        [0,0,0],
    ]

    breakers = filter(lambda x: x['ground_button']['type'] == 'circuit_breaker', valid_classifications)
    main_switches = filter(lambda x: x['ground_button']['type'] == 'main_switch', valid_classifications)
    selectors = filter(lambda x: x['ground_button']['type'] == 'selector_switch', valid_classifications)

    for breaker in breakers:
        if(breaker['ground_button']['state'] == 'on' and breaker['state_button']['state'] == 'on'):
            breaker_matrix[0][0] += 1
        elif(breaker['ground_button']['state'] == 'on' and breaker['state_button']['state'] == 'off'):
            breaker_matrix[1][0] += 1
        elif(breaker['ground_button']['state'] == 'off' and breaker['state_button']['state'] == 'on'):
            breaker_matrix[0][1] += 1
        elif(breaker['ground_button']['state'] == 'off' and breaker['state_button']['state'] == 'off'):
            breaker_matrix[1][1] += 1

    for main_switch in main_switches:
        if(main_switch['ground_button']['state'] == 'on' and main_switch['state_button']['state'] == 'on'):
            main_switch_matrix[0][0] += 1
        elif(main_switch['ground_button']['state'] == 'on' and main_switch['state_button']['state'] == 'off'):
            main_switch_matrix[1][0] += 1
        elif(main_switch['ground_button']['state'] == 'off' and main_switch['state_button']['state'] == 'on'):
            main_switch_matrix[0][1] += 1
        elif(main_switch['ground_button']['state'] == 'off' and main_switch['state_button']['state'] == 'off'):
            main_switch_matrix[1][1] += 1
    
    for selector in selectors:
        ground_state = int(selector['ground_button']['state'])
        state_state = int(selector['state_button']['state'])

        selector_matrix[ground_state][state_state] += 1
    

    breaker_fn = CIRCUIT_BREAKER_COUNT - sum(breaker_matrix[0]) - sum(breaker_matrix[1])
    main_switch_fn = MAIN_SWITCH_COUNT - sum(main_switch_matrix[0]) - sum(main_switch_matrix[1])
    selector_fn = SELECTOR_COUNT - sum(selector_matrix[0]) - sum(selector_matrix[1]) - sum(selector_matrix[2])

    return breaker_matrix, main_switch_matrix, selector_matrix, breaker_fn, main_switch_fn, selector_fn
 
    
    
    
def saveToJSON(breaker_matrix, main_switch_matrix, selector_matrix, breaker_fn, main_switch_fn, selector_fn):
    results = {
        "circuit_breaker": {
            "confusion_matrix": breaker_matrix,
            "false_negatives": breaker_fn
        },
        "main_switch": {
            "confusion_matrix": main_switch_matrix,
            "false_negatives": main_switch_fn
        },
        "selector_switch": {
            "confusion_matrix": selector_matrix,
            "false_negatives": selector_fn
        }
    }
    # Save results to JSON file, create directory if it doesn't exist
    os.makedirs("tests/Classification_test/Button_recognition_test/results", exist_ok=True)
    path = "tests/Classification_test/Button_recognition_test/results/button_state_classification_results.json"
    if(os.path.exists(path)):
        path_split = path.split(".json")
        path = path_split[0] + "_1.json"
        while(os.path.exists(path)):
            path_split = path.split("_")
            start = "_".join(path_split[:-1])
            end = path_split[-1].split(".json")[0]
            if end.isdigit():
                new_end = str(int(end) + 1)
                path =  start + "_" + new_end + ".json"

    with open(path, "w") as f:
        json.dump(results, f, indent=4)
    
    print("Saved results to tests/Classification_test/Button_recognition_test/results/button_state_classification_results.json")
    
        

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

    breaker_matrix = []
    main_switch_matrix = []
    selector_matrix = []

    breaker_fn = 0
    main_switch_fn = 0
    selector_fn = 0

    for ground_file, state_file in zip(ground_filer, state_filer):
        with open(ground_file, 'r') as f:
            ground_data = json.load(f)

        with open(state_file, 'r') as f:
            state_data = json.load(f)

        print(f"on Image: {ground_data["image_filename"]}")

        ground_data = convertGroundData(ground_data)
        
        valid_classifications = find_valid_classifications(ground_data, state_data, ground_file, state_file)

        print(f"Processed files: {ground_file} and {state_file}")
        print("-----")
        print("")
        print("Found valid classifications:")
        for classification in valid_classifications:
            print(f"State Button: {classification['state_button']}, \n Ground Button: {classification['ground_button']}, \n IoU: {classification['iou']}")
        print("")
        print("====================================")

        if len(valid_classifications) == 0:
            print("No valid classifications found in these files.")
            print("====================================")

        print("Calculating metrics...")
        new_breaker_matrix, new_main_switch_matrix, new_selector_matrix, new_breaker_fn, new_main_switch_fn, new_selector_fn = calculate_metrics(valid_classifications)

        if len(breaker_matrix) == 0:
            breaker_matrix = new_breaker_matrix
        else:
            for i in range(2):
                for j in range(2):
                    breaker_matrix[i][j] += new_breaker_matrix[i][j]    
    
        if len(main_switch_matrix) == 0:
            main_switch_matrix = new_main_switch_matrix
        else:
            for i in range(2):
                for j in range(2):
                    main_switch_matrix[i][j] += new_main_switch_matrix[i][j]
        
        if len(selector_matrix) == 0:
            selector_matrix = new_selector_matrix
        else:
            for i in range(3):
                for j in range(3):
                    selector_matrix[i][j] += new_selector_matrix[i][j]
        
        breaker_fn += new_breaker_fn
        main_switch_fn += new_main_switch_fn
        selector_fn += new_selector_fn
    
    saveToJSON(breaker_matrix, main_switch_matrix, selector_matrix, breaker_fn, main_switch_fn, selector_fn)



if __name__ == "__main__":
    main()