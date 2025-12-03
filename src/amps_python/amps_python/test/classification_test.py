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


class CallibrationTest(Node):
    def __init__(self):
        super().__init__('json_saver_node')
        qos = QoSProfile(depth=10)
        
        # classification subscription
        self.create_subscription(
            ClassifiedButtonArray,
            'object_classification_topic',
            self.callback,
            qos
        )

        # classification subscription:
        self.create_subscription(
            
        )


    def classification_callback(self, msg):
        try:
            od = message_to_ordereddict(msg)
        except Exception as e:
            self.get_logger().warn(f"Konverteringsfejl: {e}")
            return
        # Konverter OrderedDict til almindelig dict for JSON
        self.data = json.loads(json.dumps(od, default=str))
      
    
    def ground_truth_callback(self, msg):
        
        self.message_GT_number # Tjekk om dette custom topic giver en str eller int


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

