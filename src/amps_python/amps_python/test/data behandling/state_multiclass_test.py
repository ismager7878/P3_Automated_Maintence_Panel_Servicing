import json
import os

file = "tests/Classification_test/Button_recognition_test/button_data/data:/button_pose1/img1_0"
lukas_file = "tests/Classification_test/Button_recognition_test/data/data:/button_pose1/img1_0"
ground_truth = "tests/Classification_test/Button_recognition_test/Ground_truth/truth:/button_pose1/img1_0"

def grab_button_test_data(file_name):
    with open(file_name, 'r') as file:
        data = json.load(file)

    breaker_0 = []
    breaker_1 = []
    
    rotory_0  = []
    rotory_1  = []
    rotory_2  = []
    
    main_0    = []
    main_1    = []

    #on, off = 1 and 2
    # rotor = 0, 1, 2 

    for i in range(len(data)):
        data_entry = data[i]

        #grab breakers:
        if data_entry["type"] == 1 and data_entry["state"] == "off":
            breaker_0.append(data_entry["bounding_box"])
        
        if data_entry["type"] == 1 and data_entry["state"] == "on":
            breaker_1.append(data_entry["bounding_box"])
        
        # grab rotary:
        if data_entry["type"] == 2 and data_entry["state"] == "0":
            rotory_0.append(data_entry["bounding_box"])

        if data_entry["type"] == 2 and data_entry["state"] == "1":
            rotory_1.append(data_entry["bounding_box"])

        if data_entry["type"] == 2 and data_entry["state"] == "2":
            rotory_2.append(data_entry["bounding_box"])

        # grab main:
        if data_entry["type"] == 3 and data_entry["state"] == "off":
            main_0.append(data_entry["bounding_box"])

        if data_entry["type"] == 3 and data_entry["state"] == "on":
            main_1.append(data_entry["bounding_box"])
        

    return breaker_0, breaker_1, rotory_0, rotory_1, rotory_2, main_0, main_1

def grab_ground_truth(file_name):
    with open(file_name, 'r') as file:
        data = json.load(file)

    breakers  = []
    breaker_states = []

    rotary    = []
    mains     = []

    # CircuitBreaker positioner:
    breaker_1_XY = data["circuit_breaker"][0]["transformed_pos_xy"]
    breaker_2_XY = data["circuit_breaker"][1]["transformed_pos_xy"]

    # split the first breaker bounding box into 13 individual bounding boxes:
    #------------------------------------------------------------------------
    bbox = breaker_1_XY
    total_height = bbox[3] - bbox[1]
    individual_height = total_height / 13
    i_height = int(individual_height)

    for i in range(13):
        first = bbox[1] + i_height * i
        last = bbox[1] + i_height * (i + 1)
        
        newbox = [bbox[0], first, bbox[2], last]
        breakers.append(newbox)
    #------------------------------------------------------------------------
    
    breakers.append(breaker_2_XY)
    
    states_b1 = data["circuit_breaker"][0]["states"]
    states_b2 = data["circuit_breaker"][1]["states"]

    breaker_states.append(states_b1)
    breaker_states.append(states_b2) 

    # Rotary switch positioner:
    rotSwitch_1_XY = data["selector_switch"][0]["transformed_pos_xy"]
    rotSwitch_2_XY = data["selector_switch"][1]["transformed_pos_xy"]
    rotSwitch_3_XY = data["selector_switch"][2]["transformed_pos_xy"]
    rotSwitch_4_XY = data["selector_switch"][3]["transformed_pos_xy"]
    rotSwitch_5_XY = data["selector_switch"][4]["transformed_pos_xy"]
    
    rotary.append(rotSwitch_1_XY)
    rotary.append(rotSwitch_2_XY)
    rotary.append(rotSwitch_3_XY)
    rotary.append(rotSwitch_4_XY)
    rotary.append(rotSwitch_5_XY)

    # Main switch positioner:
    mainSwitch_1_XY = data["main_switch"][0]["transformed_pos_xy"]
    mainSwitch_2_XY = data["main_switch"][1]["transformed_pos_xy"]

    mains.append(mainSwitch_1_XY)
    mains.append(mainSwitch_2_XY)
    
    return breakers, breaker_states, rotary, mains

def grab_test_data(file_name):
    with open(file_name, 'r') as file:
        data = json.load(file)

    breaker = []
    rotory  = []
    main    = []

    for i in range(len(data)):
        data_entry = data[i]

        if data_entry["type"] == 1:
            breaker.append(data_entry["bounding_box"])
        
        if data_entry["type"] == 2:
            rotory.append(data_entry["bounding_box"])

        if data_entry["type"] == 3:
            main.append(data_entry["bounding_box"])

    return breaker, rotory, main

def IoU(boxA, boxB):
    # Box format: [x1, y1, x2, y2]

    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    # Compute intersection area
    inter_width  = max(0, xB - xA)
    inter_height = max(0, yB - yA)
    inter_area = inter_width * inter_height

    if inter_area == 0:
        return 0.0

    # Compute both areas
    boxA_area = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxB_area = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    # Compute IoU
    iou = inter_area / float(boxA_area + boxB_area - inter_area)
    return iou

def true_positives(test_file_path, ground_file_path):
    file_test = test_file_path
    file_ground = ground_file_path

    breaker, rotary, main = grab_test_data(file_test)
    g_breaker, breaker_states, g_rotory, g_main = grab_ground_truth(file_ground)

    b_b = [] #TP
    b_r = [] #FP
    b_m = [] #FP
  
    r_b = [] #FP
    r_r = [] #TP
    r_m = [] #FP
    
    m_b = [] #FP
    m_r = [] #FP
    m_m = [] #TP
    
    false_negative = []


    # Evaluer alle detekterede knapper
    treshold = 0.5

    for detected_breaker in breaker:
        b_iou, r_iou, m_iou = [], [], []
        
        for gt_b in g_breaker:
            b_iou.append(IoU(detected_breaker, gt_b))
        for gt_r in g_rotory:
            r_iou.append(IoU(detected_breaker, gt_r))
        for gt_m in g_main:
            m_iou.append(IoU(detected_breaker, gt_m))
        
        max_b, max_r, max_m = max(b_iou) if b_iou else 0, max(r_iou) if r_iou else 0, max(m_iou) if m_iou else 0
        best_match = max(max_b, max_r, max_m)
        
        if best_match < treshold:
            false_negative.append(detected_breaker)
        elif max_b == best_match:
            b_b.append(detected_breaker)  # TP
        elif max_r == best_match:
            b_r.append(detected_breaker)  # FP
        elif max_m == best_match:
            b_m.append(detected_breaker)  # FP

    for detected_rotary in rotary:
        b_iou, r_iou, m_iou = [], [], []
        
        for gt_b in g_breaker:
            b_iou.append(IoU(detected_rotary, gt_b))
        for gt_r in g_rotory:
            r_iou.append(IoU(detected_rotary, gt_r))
        for gt_m in g_main:
            m_iou.append(IoU(detected_rotary, gt_m))
        
        max_b, max_r, max_m = max(b_iou) if b_iou else 0, max(r_iou) if r_iou else 0, max(m_iou) if m_iou else 0
        best_match = max(max_b, max_r, max_m)
        
        if best_match < treshold:
            false_negative.append(detected_rotary)
        elif max_b == best_match:
            r_b.append(detected_rotary)  # FP
        elif max_r == best_match:
            r_r.append(detected_rotary)  # TP
        elif max_m == best_match:
            r_m.append(detected_rotary)  # FP

    for detected_main in main:
        b_iou, r_iou, m_iou = [], [], []
        
        for gt_b in g_breaker:
            b_iou.append(IoU(detected_main, gt_b))
        for gt_r in g_rotory:
            r_iou.append(IoU(detected_main, gt_r))
        for gt_m in g_main:
            m_iou.append(IoU(detected_main, gt_m))
        
        max_b, max_r, max_m = max(b_iou) if b_iou else 0, max(r_iou) if r_iou else 0, max(m_iou) if m_iou else 0
        best_match = max(max_b, max_r, max_m)
        
        if best_match < treshold:
            false_negative.append(detected_main)
        elif max_b == best_match:
            m_b.append(detected_main)  # FP
        elif max_r == best_match:
            m_r.append(detected_main)  # FP
        elif max_m == best_match:
            m_m.append(detected_main)  # TP

    return b_b, r_r, m_m


breaker_0, breaker_1, rotory_0, rotory_1, rotory_2, main_0, main_1 = grab_button_test_data(file)
b_b, r_r, m_m = true_positives(lukas_file, ground_truth)
breakers, breaker_states, rotary, mains = grab_ground_truth(ground_truth)

print(breakers)
print(breaker_states)

testable_breaker_0 = []
testable_breaker_1 = []

for i in range(len(breaker_0)):
    for j in range(len(b_b)):
        if breaker_0[i] == b_b[j]:
            testable_breaker_0.append(breaker_0[i])

for i in range(len(breaker_1)):
    for j in range(len(b_b)):
        if breaker_1[i] == b_b[j]:
            testable_breaker_0.append(breaker_1[i])

for i in range(len(testable_breaker_0)):
    for j in range(len(breakers)):
        pass
        
        

def go_through_all_data():

    root_test   = "tests/Classification_test/Button_recognition_test/data/data:"
    root_ground = "tests/Classification_test/Button_recognition_test/Ground_truth/truth:"

    test_filer = []
    for dirpath, dirnames, filenames in os.walk(root_test):
        for fil in filenames:
            test_filer.append(os.path.join(dirpath, fil))

    # Saml ground-truth-filer
    ground_filer = []
    for dirpath, dirnames, filenames in os.walk(root_ground):
        for fil in filenames:
            ground_filer.append(os.path.join(dirpath, fil))

    # Sortér hvis rækkefølgen skal matche
    test_filer.sort()
    ground_filer.sort()

    alle_rotor_knapper = []

    # Lav par (én test, én ground_truth)
    for test_fil, ground_fil in zip(test_filer, ground_filer):

        true_positives(test_fil, ground_fil)