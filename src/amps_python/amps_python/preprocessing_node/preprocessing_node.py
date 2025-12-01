import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge
import cv2 as cv
import numpy as np
from amps_cpp.msg import FrameWithPose
from sensor_msgs.msg import Image

class PreprocessingNode(Node):
    def __init__(self):
        super().__init__('preprocessing_node')
        self.get_logger().info('Preprocessing Node has been started.')

        # Subscribe to the topic publishing FrameWithPose messages
        self.subscription = self.create_subscription(FrameWithPose, 'amps_cpp/pose_estimation/frame_with_pose', self.listener_callback, 10)
        self.get_logger().info(self.subscription.topic_name + ' is subscribed.')
        
        # Create publishers for transformed depth and color images
        self.publisher_depth = self.create_publisher( Image, 'amps_python/vision/transformed_depth_image', 10)
        self.publisher_color = self.create_publisher( Image, 'amps_python/vision/transformed_color_image', 10)
        
        # Initialize CvBridge
        self.bridge = CvBridge()


    def listener_callback(self, msg):
        # Convert ROS Image message to OpenCV image
        depth_image = self.bridge.imgmsg_to_cv2(msg.depth_frame, desired_encoding='passthrough')
        color_image = self.bridge.imgmsg_to_cv2(msg.rgb_frame, desired_encoding='passthrough')
        
        # Process the depth image
        transformed_depth_image, transform_matrix = transform_depth(depth_image)
        if transform_matrix is None:
            self.get_logger().warning('Transformation matrix could not be computed. Skipping this frame.')
            return
        transformed_color_image = cv.warpPerspective(color_image, transform_matrix, (transformed_depth_image.shape[1], transformed_depth_image.shape[0]))
        
        # Convert transformed depth to ROS Image message
        transformed_depth_msg = self.bridge.cv2_to_imgmsg(transformed_depth_image, encoding="mono8")

        # Convert transformed color to ROS Image message
        transformed_color_msg = self.bridge.cv2_to_imgmsg(transformed_color_image, encoding="bgr8")
        
        # Publish the transformed image
        self.publisher_depth.publish(transformed_depth_msg)
        self.publisher_color.publish(transformed_color_msg)
        self.get_logger().info('Published transformed depth and color image')
        
def main():
    rclpy.init()
    node = PreprocessingNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

def transform_depth(img, show=False):
    # Calculate median of ROI
    adjustedImg = np.array(img, dtype=np.uint16)
    vals = adjustedImg[280:780, 70:570]
    median_of_roi = np.median(vals)
    
    # Scaling
    min_val, max_val = median_of_roi-26, median_of_roi+7
    adjustedImg = ((img.astype(np.float32) - min_val) / (max_val - min_val)) * 255
    
    # Clipping
    adjustedImg[adjustedImg < 0] = 0
    adjustedImg[adjustedImg > 255] = 0
    adjustedImg = adjustedImg.astype(np.uint8)
    if show:
        cv.imshow("Adjusted Depth Image", adjustedImg)
        cv.waitKey(0)
        cv.destroyAllWindows()
        
    # Segmentation
    _, binaryImg = cv.threshold(adjustedImg, 1, 255, cv.THRESH_BINARY)
    binaryImg = cv.medianBlur(binaryImg, 5)
    #binaryImg = cv.morphologyEx(binaryImg, cv.MORPH_CLOSE, kernel)
    #binaryImg = cv.morphologyEx(binaryImg, cv.MORPH_OPEN, kernel)
    if show:
        cv.imshow("Binary Depth Image", binaryImg)
        cv.waitKey(0)
        cv.destroyAllWindows()

    try:
        # Find contours and keep the largest
        contours, _ = cv.findContours(binaryImg, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
        largest = max(contours, key=cv.contourArea)
        #largest = sorted(contours, key=cv.contourArea)

        # Bounding box
        rect = cv.minAreaRect(largest)     # rotated rectangle
        box = cv.boxPoints(rect)           # 4 corner points
        box = np.int32(box)
        box = order_points(box)  # order points: top-left, top-right, bottom-right, bottom-left
    except Exception as ex:
        return None

    # Draw corner points and lines
    if show:
        print("Corner Points:\n", box)
        print(box[0])
        adjustedImgBGR = cv.cvtColor(adjustedImg, cv.COLOR_GRAY2BGR)
        cv.polylines(adjustedImgBGR, [box.astype(np.int32)], True, (0,255,0), 3)
        cv.imshow("Corner Points and lines", adjustedImgBGR)
        cv.waitKey(0)
        cv.destroyAllWindows()

    
    # Transformation
    corner_points = np.array(box, dtype="float32")
    dst_points = np.array([[0,0],[883,0],[883,681],[0,681]],dtype="float32")
    transform_matrix = cv.getPerspectiveTransform(corner_points, dst_points)
    warped_img = cv.warpPerspective(adjustedImg, transform_matrix, (883, 681))

    return warped_img, transform_matrix

def order_points(points):
    box = np.zeros((4,2), dtype="float32")

    sum = points.sum(axis=1)
    box[0] = points[np.argmin(sum)]     # top-left
    box[2] = points[np.argmax(sum)]     # bottom-right

    diff = np.diff(points, axis=1)
    box[1] = points[np.argmin(diff)]  # top-right
    box[3] = points[np.argmax(diff)]  # bottom-left

    return box # return the ordered coordinates like: top-left, top-right, bottom-right, bottom-left
