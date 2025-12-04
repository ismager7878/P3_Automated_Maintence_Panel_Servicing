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
from amps_cpp.msg import GroundTruthButton


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


    def classification_callback(self, msg):
        try:
            od = message_to_ordereddict(msg)
        except Exception as e:
            self.get_logger().warn(f"Konverteringsfejl: {e}")
            return
        # Konverter OrderedDict til almindelig dict for JSON
        self.data = json.loads(json.dumps(od, default=str, indent=4))
        self.get_logger().info(f"message fra lukas: {self.data}")
      
    
    def ground_truth_callback(self, msg):
        try:
            od = message_to_ordereddict(msg)
        except Exception as e:
            self.get_logger().warn(f"Konverteringsfejl: {e}")
            return
        # Konverter OrderedDict til almindelig dict for JSON
        self.data_truth = json.loads(json.dumps(od, default=str, indent=4))
        #self.get_logger().info(f"ground_truth: {self.data_truth}")
        


    def grab_classification(self):
        pass

    def grab_GT(self):
        pass



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

