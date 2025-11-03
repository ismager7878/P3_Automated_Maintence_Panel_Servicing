import json

# Example to JSON
#json.dump(data, json_file, indent=4)

# Example from JSON
#json.load(json_file)

# Ground truth dictionary example
ground_truth : dict = {
    "btn_config": "1",
    "board_state": {
        "CircuitBreaker": {
            0:"on",
            1:"off",
            2:"on",
            3:"off",
            4:"on",
            5:"on",
            6:"off",
            7:"off",
            8:"on",
            9:"on",
            10:"off",
            11:"on",
            12:"off",
            13:"on"
        },
        "SelectorSwitch": {
            0:"2",
            1:"0",
            2:"1",
            3:"0",
            4:"1"
        },
        "MainSwitch": {
            0:"off",
            1:"on"
        },
        "Plug": {
            0:"in",
            1:"out"
        }
    }
}