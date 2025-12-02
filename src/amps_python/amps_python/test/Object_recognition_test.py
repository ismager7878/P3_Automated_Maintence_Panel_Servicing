import json
import numpy as np

g_button_pose1 = 'datasets/auto_aligned_dataset/button_pose1/ground_truth.json'
t_button       = "src/amps_python/amps_python/test/prøve-json"

def test_PR(ground_truth_file_path, test_file_path):
    #Hjælpe funktioner:
    def extract_ground_truth(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)

        breakers  = []
        rotary    = []
        mains     = []
        plugs     = []

        # CircuitBreaker positioner:
        breaker_1_XY = data["board_state"]["CircuitBreaker"][0]["posXY"]
        breaker_2_XY = data["board_state"]["CircuitBreaker"][1]["posXY"]

        breakers.append(breaker_1_XY)
        breakers.append(breaker_2_XY)

        # Rotary switch positioner:
        rotSwitch_1_XY = data["board_state"]["SelectorSwitch"][0]["posXY"]
        rotSwitch_2_XY = data["board_state"]["SelectorSwitch"][1]["posXY"]
        rotSwitch_3_XY = data["board_state"]["SelectorSwitch"][2]["posXY"]
        rotSwitch_4_XY = data["board_state"]["SelectorSwitch"][3]["posXY"]
        rotSwitch_5_XY = data["board_state"]["SelectorSwitch"][4]["posXY"]

        rotary.append(rotSwitch_1_XY)
        rotary.append(rotSwitch_2_XY)
        rotary.append(rotSwitch_3_XY)
        rotary.append(rotSwitch_4_XY)
        rotary.append(rotSwitch_5_XY)

        # Main switch positioner:
        mainSwitch_1_XY = data["board_state"]["MainSwitch"][0]["posXY"]
        mainSwitch_2_XY = data["board_state"]["MainSwitch"][1]["posXY"]

        mains.append(mainSwitch_1_XY)
        mains.append(mainSwitch_2_XY)

        # Kontaks positioner:
        plug_1_XY = data["board_state"]["Plug"][0]["posXY"]
        plug_2_XY = data["board_state"]["Plug"][1]["posXY"]

        plugs.append(plug_1_XY)
        plugs.append(plug_2_XY)

        return breakers, rotary, mains, plugs

    # Træk data fra Lukases json filer:
    def extract_test_data(test_file_path):
        with open(test_file_path, 'r') as file:
            data = json.load(file)

        circuitBreaker_list = []
        selectorSwitch_list = []
        mainSwitch_list     = []
        plug_list           = []

        
        breakers = data["board_state"]["CircuitBreaker"]
        for i in range (len(breakers)):
            breaker = data["board_state"]["CircuitBreaker"][i]["posXY"]
            circuitBreaker_list.append(breaker)

        
        switches = data["board_state"]["SelectorSwitch"]
        for i in range(len(switches)):
            switches = data["board_state"]["SelectorSwitch"][i]["posXY"]
            selectorSwitch_list.append(switches)

        
        main = data["board_state"]["MainSwitch"]
        for i in range(len(main)):
            main = data["board_state"]["MainSwitch"][i]["posXY"]
            mainSwitch_list.append(main)
        
        
        plug = data["board_state"]["Plug"]
        for i in range(len(plug)):
            plug = data["board_state"]["Plug"][i]["posXY"]
            plug_list.append(plug)

        return circuitBreaker_list, selectorSwitch_list, mainSwitch_list, plug_list
    
    def look_for_classification(wrong_classification):
        ground_breaker, ground_rotary, ground_main, ground_plug = extract_ground_truth(ground_truth_file_path)

        for i in range(len(ground_breaker)):
            if wrong_classification == ground_breaker[i]:
                return "CircuitBreaker"
        
        for i in range(len(ground_rotary)):
            if wrong_classification == ground_rotary[i]:
                return "SelectorSwitch"
            
        for i in range(len(ground_main)):
            if wrong_classification == ground_main[i]:
                return "MainSwitch"
            
        for i in range(len(ground_plug)):
            if wrong_classification == ground_plug[i]:
                return "Plug"

    #----------------------------------------------------------------------------------------------------
    #Validering:

    # Ground truth værdier:
    ground_breaker, ground_rotary, ground_main, ground_plug = extract_ground_truth(ground_truth_file_path)

    breakers, rotary, mains, plugs = extract_test_data(test_file_path)

    classification_goal = len(ground_breaker) + len(ground_rotary) + len(ground_main) + len(ground_plug)

    classified = len(breakers) + len(rotary) + len(mains) + len(plugs)

    true_positive   = []
    false_positive  = []
    false_negative  = []


    print("Correct number of classification", classification_goal)
    print("number of classified objects", classified)


    # Tjekkker for false positive and true positive
    for i in range(len(breakers)):
        if breakers[i] == ground_breaker[0] or breakers[i] == ground_breaker[1]:
            print("breaker match")
            true_positive.append(breakers[i])
        else: 
            correct_classification = look_for_classification(breakers[i])
            print(f"breaker worng classification, correct classification: {correct_classification}")
            false_positive.append(breakers[i])
            

    for i in range(len(rotary)):
        if rotary[i] == ground_rotary[0] or rotary[i] == ground_rotary[1] or rotary[i] == ground_rotary[2] or rotary[i] == ground_rotary[3] or rotary[i] == ground_rotary[4]:
            print("rotary switch match")
            true_positive.append(rotary[i])
        else: 
            correct_classification = look_for_classification(rotary[i])
            print(f"rotary switch worng classification, correct classification: {correct_classification}")
            false_positive.append(rotary[i])

    for i in range(len(mains)):
        if mains[i] == ground_main[0] or mains[i] == ground_main[1]:
            print("main match")
            true_positive.append(mains[i])
        else: 
            correct_classification = look_for_classification(mains[i])
            print(f"main switch wrong classification, correct classification: {correct_classification}")
            false_positive.append(mains[i])
    
    for i in range(len(plugs)):
        if plugs[i] == ground_plug[0] or plugs[i] == ground_plug[1]:
            print("plugs match")
            true_positive.append(plugs[i])
        else: 
            correct_classification = look_for_classification(plugs[i])
            print(f"plugs worng classification, correct classification: {correct_classification}")
            false_positive.append(plugs[i])

    #Tjekke for false negatives - objekter i ground truth som IKKE blev detekteret
    for ground_item in ground_breaker:
        found = False
        for detected_plug in breakers:
            if ground_item == detected_plug:
                found = True
                break
        if not found:
            false_negative.append(ground_item)

    for ground_item in ground_rotary:
        found = False
        for detected_plug in rotary:
            if ground_item == detected_plug:
                found = True
                break
        if not found:
            false_negative.append(ground_item)

    for ground_item in ground_main:
        found = False
        for detected_plug in mains:
            if ground_item == detected_plug:
                found = True
                break
        if not found:
            false_negative.append(ground_item)
    
    for ground_item in ground_plug:
        found = False
        for detected_plug in plugs:
            if ground_item == detected_plug:
                found = True
                break
        if not found:
            false_negative.append(ground_item)

    #Precision:
    precision = len(true_positive)/(len(true_positive) + len(false_positive))

    #Recall:
    recall = len(true_positive)/(len(true_positive) + len(false_negative))

    #F1 score:
    f1_score = 2 *((precision * recall)/( precision + recall))

    print("True positives", len(true_positive))
    print("False positives", len(false_positive))
    print("False negatives", len(false_negative))

    print(f"Precision: {precision} recall: {recall} f1 score: {f1_score}")



test_PR(g_button_pose1,t_button)