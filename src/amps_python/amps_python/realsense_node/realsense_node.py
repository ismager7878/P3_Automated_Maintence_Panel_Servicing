import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2 as cv

class CameraSubscriber(Node):
    def _init_(self):
        #create node with name "camera_subscriber"
        super()._init_('camera_subscriber')
        self.bridge = CvBridge()
        #self.color and self.depth will subscribe to the realsense RGB camera and depth camera with a que of 10
        self.color = self.create_subscription(Image, '/camera/camera/color/image_raw', self.camera_show, 10)
        self.depth = self.create_subscription(Image, '/camera/camera/depth/image_rect_raw',
        self.camera_depth_show, 10)
        #This function call the RGB image but since opencv use bgr, there will be a conversion with
        self.bridge.imgmsg_to_cv2()
        
    def camera_show(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        cv.imshow('Realsense RGB', frame)
        cv.waitKey(1)
        #This function call the depth image but since opencv use bgr, there will be a conversion with
        self.bridge.imgmsg_to_cv2()
        
    def camera_depth_show(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='16UC1')
        #cv.convertScaleAbs(frame, alpha=0.3) makes sure it a 8bit, since depth image are 16-bit and opencv use 8-bit
        depth_display = cv.convertScaleAbs(frame, alpha=0.3)
        cv.imshow('Realsense depth', depth_display)
        cv.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    node = CameraSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
    cv.destroyAllWindows()
    
if __name__ == '__main__':
    main()