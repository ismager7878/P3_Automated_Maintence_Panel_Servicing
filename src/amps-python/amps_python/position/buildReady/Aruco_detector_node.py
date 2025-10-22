#Chat genereret til test
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import cv2.aruco as aruco

class Aruco_detector(Node):
    def __init__(self):
        super().__init__('video_viewer')

        # Parametre (du kan override dem fra CLI)
        self.declare_parameter('color_topic', '/camera/camera/color/image_raw')

        self.bridge = CvBridge()
        sensor_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST
        )
        
        topic = self.get_parameter('color_topic').get_parameter_value().string_value
        self.sub = self.create_subscription(Image, topic, self.on_color, sensor_qos)
        self.sub1 = self.create_subscription(Image, topic, self.dict_finder, sensor_qos)
        self.get_logger().info(f'Viser COLOR fra: {topic}')

        # Timer til at håndtere cv2.waitKey uden at blokere rclpy
        self.timer = self.create_timer(0.001, self.on_timer)

    def on_color(self, msg: Image):
        try:
            # typisk encoding: "bgr8" eller "rgb8" -> cv_bridge håndterer det
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            cv2.imshow('Color', frame)
        except Exception as e:
            self.get_logger().warn(f'Kunne ikke konvertere farvebillede: {e}')

    def on_timer(self):
        # Luk på ESC eller q
        k = cv2.waitKey(1) & 0xFF
        if k in (27, ord('q')):
            self.get_logger().info('Lukker vinduer…')
            cv2.destroyAllWindows()
            rclpy.shutdown()

   

    def dict_finder(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

            
            #Alle aruco dictionaries i opencv:
            #-------------------------------------------------------------------
            arucoDict4x4 = aruco.getPredefinedDictionary(aruco.DICT_4X4_1000)
            arucoDict5x5 = aruco.getPredefinedDictionary(aruco.DICT_5X5_1000)
            arucoDict6x6 = aruco.getPredefinedDictionary(aruco.DICT_6X6_1000)
            arucoDict7x7 = aruco.getPredefinedDictionary(aruco.DICT_7X7_1000)
            #-------------------------------------------------------------------

            libStorage = [arucoDict4x4, arucoDict5x5, arucoDict6x6, arucoDict7x7] 

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            for i in range(len(libStorage)):
                parameters = aruco.DetectorParameters_create()
                corner, ids, rejected = aruco.detectMarkers(gray, libStorage[i], parameters = parameters)
                
                if ids is not None and len(ids) > 2 and i == 0:
                    print("4x4 library is a match")    
                    return libStorage[i]
                
                if ids is not None and len(ids) > 2 and i == 1:
                    print("5x5 library is a match")
                    return libStorage[i]
                
                if ids is not None and len(ids) > 2 and i == 3:
                    print("6x6 library is a match")
                    return libStorage[i]
                
                if ids is not None and len(ids) > 2 and i == 4:
                    print("7x7 library is a match")
                    return libStorage[i]
            
            print("No matches found")
        
        except Exception as e:
            self.get_logger().warn(f'Kunne ikke konvertere farvebillede: {e}')

def main():
    rclpy.init()
    node = Aruco_detector()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        if rclpy.ok():
            rclpy.shutdown()
