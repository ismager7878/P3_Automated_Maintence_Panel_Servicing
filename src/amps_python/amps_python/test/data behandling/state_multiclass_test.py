import json
import os
from collections import namedtuple

file = "tests/Classification_test/Button_recognition_test/button_data/data:/button_pose1/img1_0"

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

breaker, rotory, main, plug = grab_test_data(file)

print(main)