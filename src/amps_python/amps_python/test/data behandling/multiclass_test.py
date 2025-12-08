import json
import os

# Lukas type: 0 = Unknown
# Lukas type: 1 = circuit_breaker
# Lukas type: 2 = selector_switch
# Lukas type: 3 = main_switch
# Lukas type: 4 = plug

def grab_ground_truth(file_name):
    with open(file_name, 'r') as file:
        data = json.load(file)

    breakers  = []
    rotary    = []
    mains     = []
    plugs     = []

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

    # Kontaks positioner:
    plug_1_XY = data["plug"][0]["transformed_pos_xy"]
    plug_2_XY = data["plug"][1]["transformed_pos_xy"]

    plugs.append(plug_1_XY)
    plugs.append(plug_2_XY)
    
    
    return breakers, rotary, mains, plugs

def grab_test_data(file_name):
    with open(file_name, 'r') as file:
        data = json.load(file)

    breaker = []
    rotory  = []
    main    = []
    plug    = []

    for i in range(len(data)):
        data_entry = data[i]

        if data_entry["type"] == 1:
            breaker.append(data_entry["bounding_box"])
        
        if data_entry["type"] == 2:
            rotory.append(data_entry["bounding_box"])

        if data_entry["type"] == 3:
            main.append(data_entry["bounding_box"])

        if data_entry["type"] == 4:
            plug.append(data_entry["bounding_box"])

    return breaker, rotory, main, plug

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


all_b_b = [] #TP
all_b_r = [] #FP
all_b_m = [] #FP
all_b_p = [] #FP

all_r_b = [] #FP
all_r_r = [] #TP
all_r_m = [] #FP
all_r_p = [] #FP

all_m_b = [] #FP
all_m_r = [] #FP
all_m_m = [] #TP
all_m_p = [] #FP

all_p_b = [] #FP
all_p_r = [] #FP
all_p_m = [] #FP
all_p_p = [] #TP

all_false_negative = []

def confucion_matrix(test_file_path, ground_file_path):
    file_test = test_file_path
    file_ground = ground_file_path

    #file_test = "tests/Classification_test/Button_recognition_test/data/data:/button_pose2/img2_0"
    #file_ground = "tests/Classification_test/Button_recognition_test/Ground_truth/truth:/button_pose2/img2_0"

    breaker, rotary, main, plug = grab_test_data(file_test)
    g_breaker, g_rotory, g_main, g_plug = grab_ground_truth(file_ground)

    b_b = [] #TP
    b_r = [] #FP
    b_m = [] #FP
    b_p = [] #FP

    r_b = [] #FP
    r_r = [] #TP
    r_m = [] #FP
    r_p = [] #FP

    m_b = [] #FP
    m_r = [] #FP
    m_m = [] #TP
    m_p = [] #FP

    p_b = [] #FP
    p_r = [] #FP
    p_m = [] #FP
    p_p = [] #TP

    false_negative = []


    # Evaluer alle detekterede knapper
    treshold = 0.5

    for detected_breaker in breaker:
        b_iou, r_iou, m_iou, p_iou = [], [], [], []
        
        for gt_b in g_breaker:
            b_iou.append(IoU(detected_breaker, gt_b))
        for gt_r in g_rotory:
            r_iou.append(IoU(detected_breaker, gt_r))
        for gt_m in g_main:
            m_iou.append(IoU(detected_breaker, gt_m))
        for gt_p in g_plug:
            p_iou.append(IoU(detected_breaker, gt_p))
        
        max_b, max_r, max_m, max_p = max(b_iou) if b_iou else 0, max(r_iou) if r_iou else 0, max(m_iou) if m_iou else 0, max(p_iou) if p_iou else 0
        best_match = max(max_b, max_r, max_m, max_p)
        
        if best_match < treshold:
            false_negative.append(detected_breaker)
        elif max_b == best_match:
            b_b.append(detected_breaker)  # TP
        elif max_r == best_match:
            b_r.append(detected_breaker)  # FP
        elif max_m == best_match:
            b_m.append(detected_breaker)  # FP
        elif max_p == best_match:
            b_p.append(detected_breaker)  # FP

    for detected_rotary in rotary:
        b_iou, r_iou, m_iou, p_iou = [], [], [], []
        
        for gt_b in g_breaker:
            b_iou.append(IoU(detected_rotary, gt_b))
        for gt_r in g_rotory:
            r_iou.append(IoU(detected_rotary, gt_r))
        for gt_m in g_main:
            m_iou.append(IoU(detected_rotary, gt_m))
        for gt_p in g_plug:
            p_iou.append(IoU(detected_rotary, gt_p))
        
        max_b, max_r, max_m, max_p = max(b_iou) if b_iou else 0, max(r_iou) if r_iou else 0, max(m_iou) if m_iou else 0, max(p_iou) if p_iou else 0
        best_match = max(max_b, max_r, max_m, max_p)
        
        if best_match < treshold:
            false_negative.append(detected_rotary)
        elif max_b == best_match:
            r_b.append(detected_rotary)  # FP
        elif max_r == best_match:
            r_r.append(detected_rotary)  # TP
        elif max_m == best_match:
            r_m.append(detected_rotary)  # FP
        elif max_p == best_match:
            r_p.append(detected_rotary)  # FP

    for detected_main in main:
        b_iou, r_iou, m_iou, p_iou = [], [], [], []
        
        for gt_b in g_breaker:
            b_iou.append(IoU(detected_main, gt_b))
        for gt_r in g_rotory:
            r_iou.append(IoU(detected_main, gt_r))
        for gt_m in g_main:
            m_iou.append(IoU(detected_main, gt_m))
        for gt_p in g_plug:
            p_iou.append(IoU(detected_main, gt_p))
        
        max_b, max_r, max_m, max_p = max(b_iou) if b_iou else 0, max(r_iou) if r_iou else 0, max(m_iou) if m_iou else 0, max(p_iou) if p_iou else 0
        best_match = max(max_b, max_r, max_m, max_p)
        
        if best_match < treshold:
            false_negative.append(detected_main)
        elif max_b == best_match:
            m_b.append(detected_main)  # FP
        elif max_r == best_match:
            m_r.append(detected_main)  # FP
        elif max_m == best_match:
            m_m.append(detected_main)  # TP
        elif max_p == best_match:
            m_p.append(detected_main)  # FP

    for detected_plug in plug:
        b_iou, r_iou, m_iou, p_iou = [], [], [], []
        
        for gt_b in g_breaker:
            b_iou.append(IoU(detected_plug, gt_b))
        for gt_r in g_rotory:
            r_iou.append(IoU(detected_plug, gt_r))
        for gt_m in g_main:
            m_iou.append(IoU(detected_plug, gt_m))
        for gt_p in g_plug:
            p_iou.append(IoU(detected_plug, gt_p))
        
        max_b, max_r, max_m, max_p = max(b_iou) if b_iou else 0, max(r_iou) if r_iou else 0, max(m_iou) if m_iou else 0, max(p_iou) if p_iou else 0
        best_match = max(max_b, max_r, max_m, max_p)
        
        if best_match < treshold:
            false_negative.append(detected_plug)
        elif max_b == best_match:
            p_b.append(detected_plug)  # FP
        elif max_r == best_match:
            p_r.append(detected_plug)  # FP
        elif max_m == best_match:
            p_m.append(detected_plug)  # FP
        elif max_p == best_match:
            p_p.append(detected_plug)  # TP

    # Beregn actual False Negatives: ground truth knapper der ikke blev matchet
    # Tæl hvor mange GT knapper der ikke har et match med IoU > threshold
    matched_gt_breakers = set()
    matched_gt_rotary = set()
    matched_gt_mains = set()
    matched_gt_plugs = set()
    
    # Find matchede ground truth knapper fra alle detektioner
    all_detections = breaker + rotary + main + plug
    for det in all_detections:
        for i, gt_b in enumerate(g_breaker):
            if IoU(det, gt_b) >= treshold:
                matched_gt_breakers.add(i)
        for i, gt_r in enumerate(g_rotory):
            if IoU(det, gt_r) >= treshold:
                matched_gt_rotary.add(i)
        for i, gt_m in enumerate(g_main):
            if IoU(det, gt_m) >= treshold:
                matched_gt_mains.add(i)
        for i, gt_p in enumerate(g_plug):
            if IoU(det, gt_p) >= treshold:
                matched_gt_plugs.add(i)
    
    # FN = GT knapper der ikke blev matchet
    unmatched_breakers = len(g_breaker) - len(matched_gt_breakers)
    unmatched_rotary = len(g_rotory) - len(matched_gt_rotary)
    unmatched_mains = len(g_main) - len(matched_gt_mains)
    unmatched_plugs = len(g_plug) - len(matched_gt_plugs)
    
    actual_FN = unmatched_breakers + unmatched_rotary + unmatched_mains + unmatched_plugs
    """
    print("------------------------------------------------------------------------------------------------------------------------------")
    print(f"file path: {test_file_path}:")
    print(f"Breaker TP: {len(b_b)}, FP as rotary: {len(b_r)}, FP as main: {len(b_m)}, FP as plug: {len(b_p)}")
    print(f"Rotary TP: {len(r_r)}, FP as breaker: {len(r_b)}, FP as main: {len(r_m)}, FP as plug: {len(r_p)}")
    print(f"Main TP: {len(m_m)}, FP as breaker: {len(m_b)}, FP as rotary: {len(m_r)}, FP as plug: {len(m_p)}")
    print(f"Plug TP: {len(p_p)}, FP as breaker: {len(p_b)}, FP as rotary: {len(p_r)}, FP as main: {len(p_m)}")
    print(f"False Negatives (no match): {actual_FN}")
    print("================================================================================================================================")
    """

    all_b_b.append(len(b_b)) 
    all_b_r.append(len(b_r))
    all_b_m.append(len(b_m))
    all_b_p.append(len(b_p))

    all_r_b.append(len(r_b))
    all_r_r.append(len(r_r))
    all_r_m.append(len(r_m))
    all_r_p.append(len(r_p))

    all_m_b.append(len(m_b))
    all_m_r.append(len(m_r))
    all_m_m.append(len(m_m))
    all_m_p.append(len(m_p))

    all_p_b.append(len(p_b))
    all_p_r.append(len(p_r))
    all_p_m.append(len(p_m))
    all_p_p.append(len(p_p))

    all_false_negative.append(actual_FN)

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

        confucion_matrix(test_fil, ground_fil)

    breaker_res = [sum(all_b_b), sum(all_b_r), sum(all_b_m), sum(all_b_p)]
    rotary_res = [sum(all_r_r), sum(all_r_b), sum(all_r_m), sum(all_r_p)]
    main_res = [sum(all_m_m), sum(all_m_b), sum(all_m_r), sum(all_m_p)]
    plug_res = [sum(all_p_p), sum(all_p_b), sum(all_p_r), sum(all_p_m)]
    fn_res = sum(all_false_negative)

    """
    print("------------------------------------------------------------------------------------------------------------------------------")
    print(f"Breaker TP: {sum(all_b_b)}, FP as rotary: {sum(all_b_r)}, FP as main: {sum(all_b_m)}, FP as plug: {sum(all_b_p)}")
    print(f"Rotary TP: {sum(all_r_r)}, FP as breaker: {sum(all_r_b)}, FP as main: {sum(all_r_m)}, FP as plug: {sum(all_r_p)}")
    print(f"Main TP: {sum(all_m_m)}, FP as breaker: {sum(all_m_b)}, FP as rotary: {sum(all_m_r)}, FP as plug: {sum(all_m_p)}")
    print(f"Plug TP: {sum(all_p_p)}, FP as breaker: {sum(all_p_b)}, FP as rotary: {sum(all_p_r)}, FP as main: {sum(all_p_m)}")
    print(f"False Negatives (no match): {sum(all_false_negative)}")
    print("================================================================================================================================")

    print(breaker_res)
    print(rotary_res)
    print(main_res)
    print(plug_res)
    print(fn_res)
    """
    
    return breaker_res, rotary_res, main_res, plug_res, fn_res

def precision_recall():
    # Plugs are not included since, they are not classified
    breaker_res, rotary_res, main_res, plug_res, fn_res = go_through_all_data()

    fp_b = breaker_res[1] + breaker_res[2] + breaker_res[3]
    fp_r = rotary_res[1] + rotary_res[2] + rotary_res[3]
    fp_m = main_res[1] + main_res[2] + main_res[3]

    true_positive = breaker_res[0] + rotary_res[0] + main_res[0] + plug_res[0]
    false_positive = fp_b + fp_r + fp_m
    false_negative = fn_res

    precision = true_positive / (true_positive + false_positive)
    recall = true_positive / (true_positive + false_negative)
    f1_score = 2 * ((precision * recall)/(precision + recall))

    return precision, recall, f1_score


def json_output(breaker, rotary, main, plug, false_negative, P, R, f1):
    data = {
        "confusion_score": {
            "breaker_score": breaker,
            "rotary_score": rotary,
            "main_score": main,
            "plug_score": plug,
            "false_negative": false_negative,
        },
        "precision": P,
        "recall": R,
        "f1": f1,
    }

    # Hvor filen skal ligge
    folder_path = "tests/Classification_test/Button_recognition_test/results/All_data"
    os.makedirs(folder_path, exist_ok=True)  # Opret mappen hvis den ikke findes

    file_path = os.path.join(folder_path, "confusion matrix 1")

    # Gem som JSON
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4) 
    print("file updated")

breaker_res, rotary_res, main_res, plug_res, fn_res = go_through_all_data()
precision, recall, f1_score = precision_recall()

json_output(breaker_res, rotary_res, main_res, plug_res, fn_res, precision, recall, f1_score)