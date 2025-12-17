import json
import numpy as np


def get_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def main():

    data = get_json("tests/Classification_test/Button_recognition_test/Report results/All_data/confusion_matrix_module.json")

    breaker = data["confusion_score"]["breaker_score"]
    rotary = data["confusion_score"]["rotary_score"]
    main = data["confusion_score"]["main_score"]


    cm1 = np.array([
        [breaker[0], breaker[1], breaker[2]],
        [rotary[1],   rotary[0], rotary[2]],
        [main[1],   main[2],  main[0]]
    ])

    breakerTP = cm1[0][0]
    breakerFN = cm1[1][0] + cm1[2][0]
    breakerFP = cm1[0][1] + cm1[0][2]

    rotaryTP = cm1[1][1]
    rotaryFN = cm1[0][1] + cm1[2][1]
    rotaryFP = cm1[1][0] + cm1[1][2]

    mainTP = cm1[2][2]
    mainFN = cm1[0][2] + cm1[1][2]
    mainFP = cm1[2][0] + cm1[2][1]

    breaker_precision = breakerTP / (breakerTP + breakerFP) if (breakerTP + breakerFP) > 0 else 0
    breaker_recall = breakerTP / (breakerTP + breakerFN) if (breakerTP + breakerFN) > 0 else 0  
    rotary_precision = rotaryTP / (rotaryTP + rotaryFP) if (rotaryTP + rotaryFP) > 0 else 0

    rotary_recall = rotaryTP / (rotaryTP + rotaryFN) if (rotaryTP + rotaryFN) > 0 else 0
    main_precision = mainTP / (mainTP + mainFP) if (mainTP + mainFP) > 0 else 0
    main_recall = mainTP / (mainTP + mainFN) if (mainTP + mainFN) > 0 else 0

    print("Circuit breaker switch - Precision: {:.2f}, Recall: {:.2f}".format(breaker_precision, breaker_recall))
    print("Rotary control switch - Precision: {:.2f}, Recall: {:.2f}".format(rotary_precision, rotary_recall))
    print("Rotary power switch - Precision: {:.2f}, Recall: {:.2f}".format(main_precision, main_recall))

    data["breaker"]["precision"] = breaker_precision
    data["breaker"]["recall"] = breaker_recall
    data["rotary"]["precision"] = rotary_precision
    data["rotary"]["recall"] = rotary_recall
    data["main"]["precision"] = main_precision
    data["main"]["recall"] = main_recall
    
    with open("tests/Classification_test/Button_recognition_test/Report results/All_data/confusion_matrix_module.json", 'w') as f:
        json.dump(data, f, indent=4)
    

if __name__ == "__main__":  
    main()


