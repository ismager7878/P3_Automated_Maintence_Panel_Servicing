import json
import os

file = "tests/Classification_test/Button_recognition_test/button_data/data:/button_pose1/img1_0"
lukas_file = "tests/Classification_test/Button_recognition_test/data/data:/button_pose1/img1_0"
ground_truth_1 = "tests/Classification_test/Button_recognition_test/Ground_truth/truth:/button_pose1/img1_0"

def grab_button_test_data(file_name):
    """
    Reads state_data file (output from button state module) and extracts button detections
    organized by type and predicted state.
    
    Returns:
        breaker_0, breaker_1, rotory_0, rotory_1, rotory_2, main_0, main_1
        Each is a list of bounding boxes for that type and state.
    """
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
    """
    Parses ground truth JSON file and extracts button bounding boxes with their states.
    
    For circuit_breakers:
      - Each circuit_breaker element has a 'transformed_pos_xy' (a single bounding box)
        and a 'states' list (one state per physical breaker in that column).
      - We split the bounding box vertically into len(states) equal-height boxes,
        assigning each sub-box its corresponding state from the states list.
      - This approach handles variable numbers of breakers per column dynamically.
    
    For selector_switch and main_switch:
      - Each element has a 'transformed_pos_xy' and a 'states' list.
      - We extract states[0] as the state string for that button.
    
    Returns:
      breaker, breaker_0, breaker_1, rotary, rotary_0, rotary_1, rotary_2, mains, main_0, main_1
      Where:
        - breaker: all breaker boxes
        - breaker_0/1: breakers with state "off"/"on"
        - rotary: all rotary boxes
        - rotary_0/1/2: rotary switches with state "0"/"1"/"2"
        - mains: all main switch boxes
        - main_0/1: main switches with state "off"/"on"
    """
    with open(file_name, 'r') as file:
        data = json.load(file)

    breaker, breaker_states = [], []
    breaker_0, breaker_1 = [], []

    rotary = []
    rotary_0, rotary_1, rotary_2 = [], [], []

    mains = []
    main_0, main_1 = [], [] 

    # ============================
    # Process circuit_breakers
    # ============================
    # Each circuit_breaker element may have multiple physical breakers (one state per breaker).
    # We split its bounding box vertically into len(states) equal parts.
    
    for cb_element in data["circuit_breaker"]:
        bbox = cb_element["transformed_pos_xy"]
        states = cb_element["states"]
        
        num_breakers = len(states)
        if num_breakers == 0:
            continue
        
        # Split bounding box vertically into num_breakers equal-height boxes
        total_height = bbox[3] - bbox[1]
        individual_height = total_height / num_breakers
        
        for i in range(num_breakers):
            y1 = bbox[1] + individual_height * i
            y2 = bbox[1] + individual_height * (i + 1)
            sub_box = [bbox[0], y1, bbox[2], y2]
            
            breaker.append(sub_box)
            breaker_states.append(states[i])
            
            # Categorize by state
            if states[i] == "off":
                breaker_0.append(sub_box)
            elif states[i] == "on":
                breaker_1.append(sub_box)
    
    # Sanity check
    if len(breaker) != len(breaker_states):
        print(f"Warning: imbalance in number of breakers: {len(breaker)} vs states: {len(breaker_states)}")
    
    # ============================
    # Process selector_switches (rotary)
    # ============================
    # Each selector_switch has a single bounding box and states[0] is the state.
    
    for rs_element in data["selector_switch"]:
        rs_box = rs_element["transformed_pos_xy"]
        rs_state = rs_element["states"][0]  # Extract first element as state string
        
        rotary.append(rs_box)
        
        if rs_state == "0":
            rotary_0.append(rs_box)
        elif rs_state == "1":
            rotary_1.append(rs_box)
        elif rs_state == "2":
            rotary_2.append(rs_box)
    
    # ============================
    # Process main_switches
    # ============================
    # Each main_switch has a single bounding box and states[0] is the state.
    
    for ms_element in data["main_switch"]:
        ms_box = ms_element["transformed_pos_xy"]
        ms_state = ms_element["states"][0]  # Extract first element as state string
        
        mains.append(ms_box)
        
        if ms_state == "off":
            main_0.append(ms_box)
        elif ms_state == "on":
            main_1.append(ms_box)
    
    return breaker, breaker_0, breaker_1, rotary, rotary_0, rotary_1, rotary_2, mains, main_0, main_1

def grab_test_data(file_name):
    """
    Reads classification output file and extracts detected buttons organized by type.
    
    Returns:
        breaker, rotory, main
        Each is a list of bounding boxes for that button type (class).
    """
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
    """
    Computes Intersection over Union (IoU) between two bounding boxes.
    
    Args:
        boxA, boxB: Bounding boxes in format [x1, y1, x2, y2]
    
    Returns:
        IoU value (float between 0 and 1)
    """
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
    """
    Identifies class-level true positives by comparing detected buttons against ground truth.
    
    For each detected button:
      1. Compute IoU against all GT boxes of each class (breaker, rotary, main)
      2. Find best match across all classes
      3. If best IoU >= threshold (0.5):
         - If best match is same class as detection → True Positive (TP)
         - If best match is different class → False Positive (FP)
         - If no match meets threshold → False Negative
    
    Args:
        test_file_path: Path to classification output file
        ground_file_path: Path to ground truth file
    
    Returns:
        b_b, r_r, m_m: Lists of TP bounding boxes for breakers, rotary, and main switches
    """
    file_test = test_file_path
    file_ground = ground_file_path

    breaker, rotary, main = grab_test_data(file_test)
    g_breaker, breaker_0, breaker_1, g_rotory, rotary_0, rotary_1, rotary_2, g_main, main_0, main_1 = grab_ground_truth(file_ground)

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



#breakers:
tp_0, fp_0, tp_1, fp_1 = [], [], [], []
#rotary:
tp_0_r, fp_0_r, tp_1_r, fp_1_r, tp_2_r, fp_2_r = [], [], [], [], [], []
#mains:
tp_0_m, fp_0_m, tp_1_m, fp_1_m = [], [], [], []


def _filter_tp_boxes(predicted_boxes, tp_boxes):
    """
    Helper function to filter predicted boxes down to those that are true positives.
    
    Since classification and state modules share identical bounding boxes for each detection,
    we can directly match boxes from state_data against the TP list from classification.
    
    Args:
        predicted_boxes: List of boxes from state_data
        tp_boxes: List of TP boxes from classification (already validated with IoU)
    
    Returns:
        List of boxes that appear in both lists (i.e., TPs for state evaluation)
    """
    testable = []
    for pred_box in predicted_boxes:
        if pred_box in tp_boxes:
            testable.append(pred_box)
    return testable


def _validate_state_predictions(predicted_boxes, predicted_state, gt_state_lists, state_names, tp_list, fp_list, threshold=0.5):
    """
    Helper function to validate state predictions against ground truth.
    
    For each predicted box with a given state:
      1. Compute IoU against all ground truth boxes for each possible state.
      2. Find the best match across all states.
      3. If best IoU >= threshold:
         - If best match is in the GT list for the predicted state → TP
         - Otherwise → FP
    
    Args:
        predicted_boxes: List of boxes with the predicted state
        predicted_state: The state being evaluated (for display/debugging)
        gt_state_lists: List of GT box lists, one per possible state
        state_names: List of state names corresponding to gt_state_lists (for debugging)
        tp_list: Global TP list to append to
        fp_list: Global FP list to append to
        threshold: IoU threshold for considering a match valid
    """
    for box in predicted_boxes:
        # Compute IoU against all GT boxes for each state
        iou_per_state = []
        for gt_list in gt_state_lists:
            ious = [IoU(box, gt_box) for gt_box in gt_list]
            max_iou = max(ious) if ious else 0
            iou_per_state.append(max_iou)
        
        # Find best match across all states
        best_iou = max(iou_per_state) if iou_per_state else 0
        
        if best_iou >= threshold:
            # Check if best match is with the predicted state (first in list)
            best_state_idx = iou_per_state.index(best_iou)
            if best_state_idx == 0:  # First GT list corresponds to predicted state
                tp_list.append(box)  # True Positive
            else:
                fp_list.append(box)  # False Positive (predicted state doesn't match GT)


def test_states(ground_truth, classification_file, state_file):
    """
    Evaluates state prediction accuracy for detections that are already true positives on the class level.
    
    Process:
      Step A - Filter to True Positives:
        1. Get state predictions from state_file (with predicted state per box)
        2. Get class-level TPs from classification_file (boxes that match GT class with IoU >= threshold)
        3. Filter state predictions to only those boxes that are class-level TPs
           (Since classification and state share identical boxes, we can match directly)
      
      Step B - Validate State Predictions:
        For each TP detection with a predicted state:
          1. Compute IoU against GT boxes for all possible states of that button type
          2. Find best match (highest IoU across all state-specific GT lists)
          3. If best IoU >= threshold:
             - If best match is with GT of the predicted state → count as TP for that state
             - If best match is with GT of a different state → count as FP for that state
    
    Updates global TP/FP lists:
      - Breakers: tp_0, fp_0, tp_1, fp_1
      - Rotary: tp_0_r, fp_0_r, tp_1_r, fp_1_r, tp_2_r, fp_2_r
      - Mains: tp_0_m, fp_0_m, tp_1_m, fp_1_m
    """
    global tp_0, fp_0, tp_1, fp_1, tp_0_r, fp_0_r, tp_1_r, fp_1_r, tp_2_r, fp_2_r, tp_0_m, fp_0_m, tp_1_m, fp_1_m

    # Load state predictions (with predicted state per box)
    breaker_0, breaker_1, rotory_0, rotory_1, rotory_2, main_0, main_1 = grab_button_test_data(state_file)
    
    # Get class-level true positives (boxes that matched GT class with IoU >= threshold)
    b_b, r_r, m_m = true_positives(classification_file, ground_truth)
    
    # Load ground truth (all boxes organized by class and state)
    g_breaker, g_breaker_0, g_breaker_1, g_rotary, g_rotary0, g_rotary1, g_rotary2, g_mains, g_main_0, g_main_1 = grab_ground_truth(ground_truth)

    # ================================================================================
    # STEP A: Filter state predictions to only class-level TRUE POSITIVES
    # ================================================================================
    # Since classification and state modules share identical bounding boxes,
    # we can directly match boxes from state_data against class-level TP lists.
    
    # Breakers: filter to only those that are class-level TPs
    testable_breaker_0 = _filter_tp_boxes(breaker_0, b_b)
    testable_breaker_1 = _filter_tp_boxes(breaker_1, b_b)
    
    # Rotary: filter to only those that are class-level TPs
    testable_rotary_0 = _filter_tp_boxes(rotory_0, r_r)
    testable_rotary_1 = _filter_tp_boxes(rotory_1, r_r)
    testable_rotary_2 = _filter_tp_boxes(rotory_2, r_r)
    
    # Mains: filter to only those that are class-level TPs
    testable_main_0 = _filter_tp_boxes(main_0, m_m)
    testable_main_1 = _filter_tp_boxes(main_1, m_m)

    # ================================================================================
    # STEP B: Validate STATE predictions for TP detections
    # ================================================================================
    # For each testable detection, compare predicted state vs ground truth state
    # using IoU against state-specific GT lists.
    
    threshold = 0.5
    
    # --- Breakers ---
    # Validate predicted state "off" (state 0)
    _validate_state_predictions(
        predicted_boxes=testable_breaker_0,
        predicted_state="off",
        gt_state_lists=[g_breaker_0, g_breaker_1],  # First list is for predicted state
        state_names=["off", "on"],
        tp_list=tp_0,
        fp_list=fp_0,
        threshold=threshold
    )
    
    # Validate predicted state "on" (state 1)
    _validate_state_predictions(
        predicted_boxes=testable_breaker_1,
        predicted_state="on",
        gt_state_lists=[g_breaker_1, g_breaker_0],  # First list is for predicted state
        state_names=["on", "off"],
        tp_list=tp_1,
        fp_list=fp_1,
        threshold=threshold
    )
    
    # --- Rotary Switches ---
    # Validate predicted state "0"
    _validate_state_predictions(
        predicted_boxes=testable_rotary_0,
        predicted_state="0",
        gt_state_lists=[g_rotary0, g_rotary1, g_rotary2],  # First list is for predicted state
        state_names=["0", "1", "2"],
        tp_list=tp_0_r,
        fp_list=fp_0_r,
        threshold=threshold
    )
    
    # Validate predicted state "1"
    _validate_state_predictions(
        predicted_boxes=testable_rotary_1,
        predicted_state="1",
        gt_state_lists=[g_rotary1, g_rotary0, g_rotary2],  # First list is for predicted state
        state_names=["1", "0", "2"],
        tp_list=tp_1_r,
        fp_list=fp_1_r,
        threshold=threshold
    )
    
    # Validate predicted state "2"
    _validate_state_predictions(
        predicted_boxes=testable_rotary_2,
        predicted_state="2",
        gt_state_lists=[g_rotary2, g_rotary0, g_rotary1],  # First list is for predicted state
        state_names=["2", "0", "1"],
        tp_list=tp_2_r,
        fp_list=fp_2_r,
        threshold=threshold
    )
    
    # --- Main Switches ---
    # Validate predicted state "off" (state 0)
    _validate_state_predictions(
        predicted_boxes=testable_main_0,
        predicted_state="off",
        gt_state_lists=[g_main_0, g_main_1],  # First list is for predicted state
        state_names=["off", "on"],
        tp_list=tp_0_m,
        fp_list=fp_0_m,
        threshold=threshold
    )
    
    # Validate predicted state "on" (state 1)
    _validate_state_predictions(
        predicted_boxes=testable_main_1,
        predicted_state="on",
        gt_state_lists=[g_main_1, g_main_0],  # First list is for predicted state
        state_names=["on", "off"],
        tp_list=tp_1_m,
        fp_list=fp_1_m,
        threshold=threshold
    )   


def go_through_all_data():

    root_test   = "tests/Classification_test/Button_recognition_test/data/data:"
    root_ground = "tests/Classification_test/Button_recognition_test/Ground_truth/truth:"
    root_state  = "tests/Classification_test/Button_recognition_test/button_data/data:"

    test_filer = []
    for dirpath, dirnames, filenames in os.walk(root_test):
        for fil in filenames:
            test_filer.append(os.path.join(dirpath, fil))

    # Saml ground-truth-filer
    ground_filer = []
    for dirpath, dirnames, filenames in os.walk(root_ground):
        for fil in filenames:
            ground_filer.append(os.path.join(dirpath, fil))

    state_filer = []
    for dirpath, dirnames, filenames in os.walk(root_state):
        for fil in filenames:
            state_filer.append(os.path.join(dirpath, fil))

    # Sortér hvis rækkefølgen skal matche
    test_filer.sort()
    ground_filer.sort()
    state_filer.sort()
    
    # Lav par (én test, én ground_truth)
    for test_fil, ground_fil, state_fil in zip(test_filer, ground_filer, state_filer):
        test_states(ground_fil, test_fil, state_fil)

    print(len(state_filer))
    print(len(ground_filer))

    # ================================================================================
    # RESULTS SUMMARY
    # ================================================================================
    print("\n" + "="*80)
    print("STATE EVALUATION RESULTS")
    print("="*80)
    
    # --- Breakers ---
    print("\n--- CIRCUIT BREAKERS ---")
    print(f"State 'OFF' (0):")
    print(f"  True Positives:  {len(tp_0)}")
    print(f"  False Positives: {len(fp_0)}")
    total_pred_0 = len(tp_0) + len(fp_0)
    accuracy_0 = (len(tp_0) / total_pred_0 * 100) if total_pred_0 > 0 else 0
    print(f"  Accuracy: {accuracy_0:.2f}% ({len(tp_0)}/{total_pred_0})")
    
    print(f"\nState 'ON' (1):")
    print(f"  True Positives:  {len(tp_1)}")
    print(f"  False Positives: {len(fp_1)}")
    total_pred_1 = len(tp_1) + len(fp_1)
    accuracy_1 = (len(tp_1) / total_pred_1 * 100) if total_pred_1 > 0 else 0
    print(f"  Accuracy: {accuracy_1:.2f}% ({len(tp_1)}/{total_pred_1})")
    
    total_breakers = total_pred_0 + total_pred_1
    total_tp_breakers = len(tp_0) + len(tp_1)
    overall_accuracy_breakers = (total_tp_breakers / total_breakers * 100) if total_breakers > 0 else 0
    print(f"\nOverall Breaker State Accuracy: {overall_accuracy_breakers:.2f}% ({total_tp_breakers}/{total_breakers})")
    
    # --- Rotary Switches ---
    print("\n--- ROTARY SWITCHES (SELECTOR) ---")
    print(f"State '0':")
    print(f"  True Positives:  {len(tp_0_r)}")
    print(f"  False Positives: {len(fp_0_r)}")
    total_pred_0_r = len(tp_0_r) + len(fp_0_r)
    accuracy_0_r = (len(tp_0_r) / total_pred_0_r * 100) if total_pred_0_r > 0 else 0
    print(f"  Accuracy: {accuracy_0_r:.2f}% ({len(tp_0_r)}/{total_pred_0_r})")
    
    print(f"\nState '1':")
    print(f"  True Positives:  {len(tp_1_r)}")
    print(f"  False Positives: {len(fp_1_r)}")
    total_pred_1_r = len(tp_1_r) + len(fp_1_r)
    accuracy_1_r = (len(tp_1_r) / total_pred_1_r * 100) if total_pred_1_r > 0 else 0
    print(f"  Accuracy: {accuracy_1_r:.2f}% ({len(tp_1_r)}/{total_pred_1_r})")
    
    print(f"\nState '2':")
    print(f"  True Positives:  {len(tp_2_r)}")
    print(f"  False Positives: {len(fp_2_r)}")
    total_pred_2_r = len(tp_2_r) + len(fp_2_r)
    accuracy_2_r = (len(tp_2_r) / total_pred_2_r * 100) if total_pred_2_r > 0 else 0
    print(f"  Accuracy: {accuracy_2_r:.2f}% ({len(tp_2_r)}/{total_pred_2_r})")
    
    total_rotary = total_pred_0_r + total_pred_1_r + total_pred_2_r
    total_tp_rotary = len(tp_0_r) + len(tp_1_r) + len(tp_2_r)
    overall_accuracy_rotary = (total_tp_rotary / total_rotary * 100) if total_rotary > 0 else 0
    print(f"\nOverall Rotary State Accuracy: {overall_accuracy_rotary:.2f}% ({total_tp_rotary}/{total_rotary})")
    
    # --- Main Switches ---
    print("\n--- MAIN SWITCHES ---")
    print(f"State 'OFF' (0):")
    print(f"  True Positives:  {len(tp_0_m)}")
    print(f"  False Positives: {len(fp_0_m)}")
    total_pred_0_m = len(tp_0_m) + len(fp_0_m)
    accuracy_0_m = (len(tp_0_m) / total_pred_0_m * 100) if total_pred_0_m > 0 else 0
    print(f"  Accuracy: {accuracy_0_m:.2f}% ({len(tp_0_m)}/{total_pred_0_m})")
    
    print(f"\nState 'ON' (1):")
    print(f"  True Positives:  {len(tp_1_m)}")
    print(f"  False Positives: {len(fp_1_m)}")
    total_pred_1_m = len(tp_1_m) + len(fp_1_m)
    accuracy_1_m = (len(tp_1_m) / total_pred_1_m * 100) if total_pred_1_m > 0 else 0
    print(f"  Accuracy: {accuracy_1_m:.2f}% ({len(tp_1_m)}/{total_pred_1_m})")
    
    total_main = total_pred_0_m + total_pred_1_m
    total_tp_main = len(tp_0_m) + len(tp_1_m)
    overall_accuracy_main = (total_tp_main / total_main * 100) if total_main > 0 else 0
    print(f"\nOverall Main Switch State Accuracy: {overall_accuracy_main:.2f}% ({total_tp_main}/{total_main})")
    
    # --- Overall Summary ---
    print("\n" + "="*80)
    print("OVERALL SUMMARY")
    print("="*80)
    total_predictions = total_breakers + total_rotary + total_main
    total_tp = total_tp_breakers + total_tp_rotary + total_tp_main
    total_fp = (len(fp_0) + len(fp_1) + len(fp_0_r) + len(fp_1_r) + len(fp_2_r) + 
                len(fp_0_m) + len(fp_1_m))
    overall_accuracy = (total_tp / total_predictions * 100) if total_predictions > 0 else 0
    print(f"Total State Predictions Evaluated: {total_predictions}")
    print(f"Total True Positives:  {total_tp}")
    print(f"Total False Positives: {total_fp}")
    print(f"Overall State Accuracy: {overall_accuracy:.2f}%")
    print("="*80 + "\n")

go_through_all_data()