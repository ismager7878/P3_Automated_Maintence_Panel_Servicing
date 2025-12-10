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
    rotary  = []
    main    = []
    plug    = []

    for i in range(len(data)):
        data_entry = data[i]

        if data_entry["type"] == 1:
            breaker.append(data_entry["bounding_box"])
        
        if data_entry["type"] == 2:
            rotary.append(data_entry["bounding_box"])

        if data_entry["type"] == 3:
            main.append(data_entry["bounding_box"])

        if data_entry["type"] == 4:
            plug.append(data_entry["bounding_box"])

    return breaker, rotary, main, plug

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

all_r_b = [] #FP
all_r_r = [] #TP
all_r_m = [] #FP

all_m_b = [] #FP
all_m_r = [] #FP
all_m_m = [] #TP

# Track False Negatives per class (unmatched GT objects)
all_fn_breaker = []
all_fn_rotary = []
all_fn_main = []


def confusion_matrix(test_file_path, ground_file_path):
    file_test = test_file_path
    file_ground = ground_file_path

    breaker, rotary, main, plug = grab_test_data(file_test)
    g_breaker, g_rotary, g_main, g_plug = grab_ground_truth(file_ground)

    b_b = [] #TP
    b_r = [] #FP
    b_m = [] #FP

    r_b = [] #FP
    r_r = [] #TP
    r_m = [] #FP

    m_b = [] #FP
    m_r = [] #FP
    m_m = [] #TP

    # Track which ground truth objects have been matched
    matched_gt_breakers = set()
    matched_gt_rotary = set()
    matched_gt_mains = set()
    
    # Evaluer alle detekterede knapper
    treshold = 0.5

    for detected_breaker in breaker:
        b_iou, r_iou, m_iou, p_iou = [], [], [], []
        
        for gt_b in g_breaker:
            b_iou.append(IoU(detected_breaker, gt_b))
        for gt_r in g_rotary:
            r_iou.append(IoU(detected_breaker, gt_r))
        for gt_m in g_main:
            m_iou.append(IoU(detected_breaker, gt_m))
        for gt_p in g_plug:
            p_iou.append(IoU(detected_breaker, gt_p))
        
        max_b, max_r, max_m, max_p = max(b_iou) if b_iou else 0, max(r_iou) if r_iou else 0, max(m_iou) if m_iou else 0, max(p_iou) if p_iou else 0
        best_match = max(max_b, max_r, max_m, max_p)
        
        if best_match < treshold:
            pass  # Unmatched detection (ignored - not counted as FP or TP)
        elif max_b == best_match:
            b_b.append(detected_breaker)  # TP - correctly classified as breaker
            # Mark the matched GT breaker
            matched_idx = b_iou.index(max_b)
            matched_gt_breakers.add(matched_idx)
        elif max_r == best_match:
            b_r.append(detected_breaker)  # FP - classified as breaker but is rotary
            # Mark the matched GT rotary (it was detected, just misclassified)
            matched_idx = r_iou.index(max_r)
            matched_gt_rotary.add(matched_idx)
        elif max_m == best_match:
            b_m.append(detected_breaker)  # FP - classified as breaker but is main
            # Mark the matched GT main (it was detected, just misclassified)
            matched_idx = m_iou.index(max_m)
            matched_gt_mains.add(matched_idx)

    for detected_rotary in rotary:
        b_iou, r_iou, m_iou, p_iou = [], [], [], []
        
        for gt_b in g_breaker:
            b_iou.append(IoU(detected_rotary, gt_b))
        for gt_r in g_rotary:
            r_iou.append(IoU(detected_rotary, gt_r))
        for gt_m in g_main:
            m_iou.append(IoU(detected_rotary, gt_m))
        for gt_p in g_plug:
            p_iou.append(IoU(detected_rotary, gt_p))
        
        max_b, max_r, max_m, max_p = max(b_iou) if b_iou else 0, max(r_iou) if r_iou else 0, max(m_iou) if m_iou else 0, max(p_iou) if p_iou else 0
        best_match = max(max_b, max_r, max_m, max_p)
        
        if best_match < treshold:
            pass  # Unmatched detection (ignored - not counted as FP or TP)
        elif max_b == best_match:
            r_b.append(detected_rotary)  # FP - classified as rotary but is breaker
            # Mark the matched GT breaker (it was detected, just misclassified)
            matched_idx = b_iou.index(max_b)
            matched_gt_breakers.add(matched_idx)
        elif max_r == best_match:
            r_r.append(detected_rotary)  # TP - correctly classified as rotary
            # Mark the matched GT rotary
            matched_idx = r_iou.index(max_r)
            matched_gt_rotary.add(matched_idx)
        elif max_m == best_match:
            r_m.append(detected_rotary)  # FP - classified as rotary but is main
            # Mark the matched GT main (it was detected, just misclassified)
            matched_idx = m_iou.index(max_m)
            matched_gt_mains.add(matched_idx)

    for detected_main in main:
        b_iou, r_iou, m_iou, p_iou = [], [], [], []
        
        for gt_b in g_breaker:
            b_iou.append(IoU(detected_main, gt_b))
        for gt_r in g_rotary:
            r_iou.append(IoU(detected_main, gt_r))
        for gt_m in g_main:
            m_iou.append(IoU(detected_main, gt_m))
        for gt_p in g_plug:
            p_iou.append(IoU(detected_main, gt_p))
        
        max_b, max_r, max_m, max_p = max(b_iou) if b_iou else 0, max(r_iou) if r_iou else 0, max(m_iou) if m_iou else 0, max(p_iou) if p_iou else 0
        best_match = max(max_b, max_r, max_m, max_p)
        
        if best_match < treshold:
            pass  # Unmatched detection (ignored - not counted as FP or TP)
        elif max_b == best_match:
            m_b.append(detected_main)  # FP - classified as main but is breaker
            # Mark the matched GT breaker (it was detected, just misclassified)
            matched_idx = b_iou.index(max_b)
            matched_gt_breakers.add(matched_idx)
        elif max_r == best_match:
            m_r.append(detected_main)  # FP - classified as main but is rotary
            # Mark the matched GT rotary (it was detected, just misclassified)
            matched_idx = r_iou.index(max_r)
            matched_gt_rotary.add(matched_idx)
        elif max_m == best_match:
            m_m.append(detected_main)  # TP - correctly classified as main
            # Mark the matched GT main
            matched_idx = m_iou.index(max_m)
            matched_gt_mains.add(matched_idx)

    # Calculate False Negatives per class: GT objects that were NOT matched
    # FN = ground truth objects that were not detected at all
    fn_breaker = len(g_breaker) - len(matched_gt_breakers)
    fn_rotary = len(g_rotary) - len(matched_gt_rotary)
    fn_main = len(g_main) - len(matched_gt_mains)
    
    # Note: Plugs are ignored in classification (as specified in requirements)

    all_b_b.append(len(b_b)) 
    all_b_r.append(len(b_r))
    all_b_m.append(len(b_m))

    all_r_b.append(len(r_b))
    all_r_r.append(len(r_r))
    all_r_m.append(len(r_m))

    all_m_b.append(len(m_b))
    all_m_r.append(len(m_r))
    all_m_m.append(len(m_m))

    # Accumulate FN per class
    all_fn_breaker.append(fn_breaker)
    all_fn_rotary.append(fn_rotary)
    all_fn_main.append(fn_main)

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

    # Lav par (én test, én ground_truth)
    for test_fil, ground_fil in zip(test_filer, ground_filer):

        confusion_matrix(test_fil, ground_fil)

    breaker_res = [sum(all_b_b), sum(all_b_r), sum(all_b_m)]
    rotary_res = [sum(all_r_r), sum(all_r_b), sum(all_r_m)]
    main_res = [sum(all_m_m), sum(all_m_b), sum(all_m_r)]
    fn_breaker_res = sum(all_fn_breaker)
    fn_rotary_res = sum(all_fn_rotary)
    fn_main_res = sum(all_fn_main)
    
    return breaker_res, rotary_res, main_res, fn_breaker_res, fn_rotary_res, fn_main_res

def precision_recall():
    # Plugs are not included since they are not classified
    breaker_res, rotary_res, main_res, fn_breaker_res, fn_rotary_res, fn_main_res = go_through_all_data()

    # For breaker: TP = b_b, FP = b_r + b_m (detections classified as breaker but wrong)
    tp_breaker = breaker_res[0]  # b_b (correctly classified as breaker)
    fp_breaker = breaker_res[1] + breaker_res[2]  # b_r + b_m (wrongly classified as breaker)
    fn_breaker = fn_breaker_res  # GT breakers that were NOT detected
    
    # For rotary: TP = r_r, FP = r_b + r_m
    tp_rotary = rotary_res[0]  # r_r (correctly classified as rotary)
    fp_rotary = rotary_res[1] + rotary_res[2]  # r_b + r_m (wrongly classified as rotary)
    fn_rotary = fn_rotary_res  # GT rotary switches that were NOT detected
    
    # For main: TP = m_m, FP = m_b + m_r
    tp_main = main_res[0]  # m_m (correctly classified as main)
    fp_main = main_res[1] + main_res[2]  # m_b + m_r (wrongly classified as main)
    fn_main = fn_main_res  # GT main switches that were NOT detected
    
    # Calculate precision for each class: Precision = TP / (TP + FP)
    # Precision measures: of all detections classified as X, how many are correct?
    precision_breaker = tp_breaker / (tp_breaker + fp_breaker) if (tp_breaker + fp_breaker) > 0 else 0
    precision_rotary = tp_rotary / (tp_rotary + fp_rotary) if (tp_rotary + fp_rotary) > 0 else 0
    precision_main = tp_main / (tp_main + fp_main) if (tp_main + fp_main) > 0 else 0
    
    # Calculate recall for each class: Recall = TP / (TP + FN)
    # Recall measures: of all GT objects of class X, how many did we detect correctly?
    recall_breaker = tp_breaker / (tp_breaker + fn_breaker) if (tp_breaker + fn_breaker) > 0 else 0
    recall_rotary = tp_rotary / (tp_rotary + fn_rotary) if (tp_rotary + fn_rotary) > 0 else 0
    recall_main = tp_main / (tp_main + fn_main) if (tp_main + fn_main) > 0 else 0

    return (precision_breaker, recall_breaker, precision_rotary, recall_rotary, precision_main, recall_main)


def json_output(breaker, rotary, main, fn_breaker, fn_rotary, fn_main, P_b, R_b, P_r, R_r, P_m, R_m):
    data = {
        "confusion_score": {
            "breaker_score": breaker,
            "rotary_score": rotary,
            "main_score": main,
            "false_negative": {
                "breaker": fn_breaker,
                "rotary": fn_rotary,
                "main": fn_main
            }
        },
        "breaker": {
            "precision": P_b,
            "recall": R_b
        },
        "rotary": {
            "precision": P_r,
            "recall": R_r
        },
        "main": {
            "precision": P_m,
            "recall": R_m
        }
    }

    # Hvor filen skal ligge
    folder_path = "tests/Classification_test/Button_recognition_test/results/All_data"
    os.makedirs(folder_path, exist_ok=True)  # Opret mappen hvis den ikke findes

    file_path = os.path.join(folder_path, "confusion_matrix_results.json")

    # Gem som JSON
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4) 
    print(f"Results saved to {file_path}")

breaker_res, rotary_res, main_res, fn_breaker_res, fn_rotary_res, fn_main_res = go_through_all_data()
precision_b, recall_b, precision_r, recall_r, precision_m, recall_m = precision_recall()

json_output(breaker_res, rotary_res, main_res, fn_breaker_res, fn_rotary_res, fn_main_res, precision_b, recall_b, precision_r, recall_r, precision_m, recall_m)