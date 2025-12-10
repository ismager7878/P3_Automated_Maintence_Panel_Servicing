import json
import os
import rclpy
from rclpy.node import Node
from datetime import datetime
from rclpy.qos import QoSProfile
# fra rosidl_runtime_py eller rclpy_message_converter
from rosidl_runtime_py.convert import message_to_ordereddict
from amps_cpp.msg import ClassifiedButtonsArray
from amps_cpp.msg import GroundTruth


class CallibrationTest(Node):
    def __init__(self):
        super().__init__('json_saver_node')
        qos = QoSProfile(depth=10)
        
        # classification subscription
        self.create_subscription(
            ClassifiedButtonsArray,
            'object_classification_topic',
            self.classification_callback,
            qos
        )

        # Groundtruth subscription:
        self.create_subscription(
            GroundTruth,
            "amps/ground_truth",
            self.ground_truth_callback,
            qos
        )
        self.get_logger().info("Noden kører :)")

        self.frame_id = 0

        # stier til mapperne
        self.test_folder = "tests/Classification_test/Button_recognition_test/data"
        self.ground_truth_folder = "tests/Classification_test/Button_recognition_test/Ground_truth"     

        self.data_id = None
        self.ground_truth = None


    def classification_callback(self, msg):
            buttons_list = []

            for btn in msg.buttons:
                buttons_list.append({
                    "type": btn.type,
                    "state": btn.state,
                    "bounding_box": list(btn.bounding_box),
                    "dot_position": list(btn.dot_position)
                })

            #filename_data = os.path.join(self.test_folder, f"classification_{self.frame_id}")
            #filename_ground = os.path.join(self.ground_truth_folder, f"btn_cf:{self.btn_config}_img:{self.frame_id}")

            filename_data = os.path.join(self.test_folder, f"data:{self.data_id}")
            #filename_ground = os.path.join(self.ground_truth_folder, f"truth:{self.data_id}")

            # Opret mappen hvis den ikke eksisterer
            os.makedirs(os.path.dirname(filename_data), exist_ok=True)
            #os.makedirs(os.path.dirname(filename_ground), exist_ok=True)

            with open(filename_data, "w") as f:
                json.dump(buttons_list, f, indent=2)

            self.get_logger().info(f"Saved: {filename_data}")
            self.frame_id += 1

            # if self.ground_truth is not None:
            #     with open(filename_ground, "w") as f:
            #         json.dump(self.ground_truth, f, indent=2)
            #     self.get_logger().info(f"Saved: {filename_ground}")
            # else:
            #     self.get_logger().warn("Ingen ground truth data endnu")
        
    
    def ground_truth_callback(self, msg):
        image_filename = msg.image_filename
        self.btn_config     = msg.btn_config
        self.ground_truth = message_to_ordereddict(msg)  # hele beskeden som nested dic
        #self.get_logger().error(self.image_filename)

        prefix = "datasets/auto_aligned_dataset"
        self.data_id = image_filename[len(prefix):]   

    
def main(args=None):
    rclpy.init(args=args)
    node = CallibrationTest()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

