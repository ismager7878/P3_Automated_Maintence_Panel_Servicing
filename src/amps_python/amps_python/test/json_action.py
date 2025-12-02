import json
import os
import rclpy
from rclpy.node import Node
from datetime import datetime
from rclpy.qos import QoSProfile
# fra rosidl_runtime_py eller rclpy_message_converter
from rosidl_runtime_py.convert import message_to_ordereddict
from amps_cpp.msg import ClassifiedButtonArray
from amps_cpp.msg import ClassifiedButton


class JsonSaverNode(Node):
    def __init__(self):
        super().__init__('json_saver_node')
        qos = QoSProfile(depth=10)
        
        self.create_subscription(
            ClassifiedButtonArray,
            'object_classification_topic',
            self.callback,
            qos
        )

        self.button_configs = [1, 2, 2, 1, 2, 1, 2, 3, 2, 2]
        self.ground_truth_number = -1

        self.filename = None
        self.goal_folder = None
        self.count = None

        self.paths = [
        "src/amps_python/amps_python/test/test_json/ground_1",
        "src/amps_python/amps_python/test/test_json/ground_2",
        "src/amps_python/amps_python/test/test_json/ground_3",
        "src/amps_python/amps_python/test/test_json/ground_4",
        "src/amps_python/amps_python/test/test_json/ground_5",
        "src/amps_python/amps_python/test/test_json/ground_6",
        "src/amps_python/amps_python/test/test_json/ground_7",
        "src/amps_python/amps_python/test/test_json/ground_8",
        "src/amps_python/amps_python/test/test_json/ground_9",
        "src/amps_python/amps_python/test/test_json/ground_10"]

        os.makedirs(self.paths[0], exist_ok=True)
        os.makedirs(self.paths[1], exist_ok=True)
        os.makedirs(self.paths[2], exist_ok=True)
        os.makedirs(self.paths[3], exist_ok=True)
        os.makedirs(self.paths[4], exist_ok=True)
        os.makedirs(self.paths[5], exist_ok=True)
        os.makedirs(self.paths[6], exist_ok=True)
        os.makedirs(self.paths[7], exist_ok=True)
        os.makedirs(self.paths[8], exist_ok=True)
        os.makedirs(self.paths[9], exist_ok=True)

    def callback(self, msg):
        try:
            od = message_to_ordereddict(msg)
        except Exception as e:
            self.get_logger().warn(f"Konverteringsfejl: {e}")
            return
        # Konverter OrderedDict til almindelig dict for JSON
        self.data = json.loads(json.dumps(od, default=str))

        self.count = len(os.listdir(self.goal_folder))
        
        self.filename = os.path.join(self.goal_folder, f"test.json{self.count + 1}")
        with open(self.filename, "w") as f:
            json.dump(self.data, f, indent=4)

        self.check_folder_sizes()

    
    def ground_truth_callback(self, msg):
        
        self.message_GT_number # Tjekk om dette custom topic giver en str eller int

        self.goal_folder = self.paths[self.message_GT_number]

    def check_folder_sizes(self):

        for i in range(len(self.paths)):
            folder_size = len(os.listdir(self.paths[i]))
            
            if folder_size == self.button_configs[i]:
                self.get_logger().warn(f"correct amount of files in folder: {i}")
            
            elif folder_size > self.button_configs[i]:
                self.get_logger().warn(f"Too many files in folder: {i}")

            elif folder_size < self.button_configs[i]:
                self.get_logger().warn(f"Folder: {i} has not been filled yet ;)")

def main(args=None):
    rclpy.init(args=args)
    node = JsonSaverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

