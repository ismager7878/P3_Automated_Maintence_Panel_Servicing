import json



def get_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def main():
    
    # Load the JSON data
    data = get_json("tests/Classification_test/Button_recognition_test/Report results/button_state_classification_results_module.json")

    breakerMatrix = data["circuit_breaker"]["confusion_matrix"]
    mainPowerMatrix = data["main_switch"]["confusion_matrix"]
    selectorMatirx = data["selector_switch"]["confusion_matrix"]

    breakerOnTP = breakerMatrix[0][0]
    breakerOnFN = breakerMatrix[1][0]
    breakerONFP = breakerMatrix[0][1]

    breakerOFFTP = breakerMatrix[1][1]
    breakerOFFFN = breakerMatrix[0][1]
    breakerOFFFP = breakerMatrix[1][0]

    mainPowerOnTP = mainPowerMatrix[0][0]
    mainPowerOnFN = mainPowerMatrix[1][0]
    mainPowerONFP = mainPowerMatrix[0][1]

    mainPowerOFFTP = mainPowerMatrix[1][1]
    mainPowerOFFFN = mainPowerMatrix[0][1]
    mainPowerOFFFP = mainPowerMatrix[1][0]

    selector1TP = selectorMatirx[0][0]
    selector1FN = selectorMatirx[1][0] + selectorMatirx[2][0]
    selector1FP = selectorMatirx[0][1] + selectorMatirx[0][2]

    selector2TP = selectorMatirx[1][1]
    selector2FN = selectorMatirx[0][1] + selectorMatirx[2][1]
    selector2FP = selectorMatirx[1][0] + selectorMatirx[1][2]

    selector3TP = selectorMatirx[2][2]
    selector3FN = selectorMatirx[0][2] + selectorMatirx[1][2]
    selector3FP = selectorMatirx[2][0] + selectorMatirx[2][1]   

    breaker_precision_on = breakerOnTP / (breakerOnTP + breakerONFP) if (breakerOnTP + breakerONFP) > 0 else 0
    breaker_recall_on = breakerOnTP / (breakerOnTP + breakerOnFN) if (breakerOnTP + breakerOnFN) > 0 else 0

    breaker_precision_off = breakerOFFTP / (breakerOFFTP + breakerOFFFP) if (breakerOFFTP + breakerOFFFP) > 0 else 0
    breaker_recall_off = breakerOFFTP / (breakerOFFTP + breakerOFFFN) if (breakerOFFTP + breakerOFFFN) > 0 else 0
    
    breaker_precision_avg = (breaker_precision_on + breaker_precision_off) / 2
    breaker_recall_avg = (breaker_recall_on + breaker_recall_off) / 2

    mainPower_precision_on = mainPowerOnTP / (mainPowerOnTP + mainPowerONFP) if (mainPowerOnTP + mainPowerONFP) > 0 else 0
    mainPower_recall_on = mainPowerOnTP / (mainPowerOnTP + mainPowerOnFN) if (mainPowerOnTP + mainPowerOnFN) > 0 else 0
    mainPower_precision_off = mainPowerOFFTP / (mainPowerOFFTP + mainPowerOFFFP) if (mainPowerOFFTP + mainPowerOFFFP) > 0 else 0
    mainPower_recall_off = mainPowerOFFTP / (mainPowerOFFTP + mainPowerOFFFN) if (mainPowerOFFTP + mainPowerOFFFN) > 0 else 0
    mainPower_precision_avg = (mainPower_precision_on + mainPower_precision_off) / 2
    mainPower_recall_avg = (mainPower_recall_on + mainPower_recall_off) / 2 

    selector1_precision = selector1TP / (selector1TP + selector1FP) if (selector1TP + selector1FP) > 0 else 0
    selector1_recall = selector1TP / (selector1TP + selector1FN) if (selector1TP + selector1FN) > 0 else 0
    selector2_precision = selector2TP / (selector2TP + selector2FP) if (selector2TP + selector2FP) > 0 else 0
    selector2_recall = selector2TP / (selector2TP + selector2FN)    
    selector3_precision = selector3TP / (selector3TP + selector3FP) if (selector3TP + selector3FP) > 0 else 0
    selector3_recall = selector3TP / (selector3TP + selector3FN) if (selector3TP + selector3FN) > 0 else 0

    selector_precision_avg = (selector1_precision + selector2_precision + selector3_precision) / 3
    selector_recall_avg = (selector1_recall + selector2_recall + selector3_recall) / 3


    data["circuit_breaker"]["precision_avg"] = breaker_precision_avg
    data["circuit_breaker"]["recall_avg"] = breaker_recall_avg

    data["main_switch"]["precision_avg"] = mainPower_precision_avg
    data["main_switch"]["recall_avg"] = mainPower_recall_avg

    data["selector_switch"]["precision_avg"] = selector_precision_avg
    data["selector_switch"]["recall_avg"] = selector_recall_avg

    # Save the updated data back to the JSON file owerwrite
    with open("tests/Classification_test/Button_recognition_test/Report results/button_state_classification_results_module.json", 'w') as f:
        json.dump(data, f, indent=4)
        
    # Print the loaded data
    print(data)

if __name__ == "__main__":
    main()



