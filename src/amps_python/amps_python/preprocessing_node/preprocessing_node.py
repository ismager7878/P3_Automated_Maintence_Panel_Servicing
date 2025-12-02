import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge
import cv2 as cv
import numpy as np
from amps_cpp.msg import FrameWithPose, CroppedImgDebug, ClassifiedButton
from sensor_msgs.msg import Image
import json, csv, os

class PreprocessingNode(Node):
    def __init__(self):
        super().__init__('preprocessing_node')
        self.declare_parameter('debugging', True)
        self.get_logger().info('Preprocessing Node has been started.')

        # Subscribe to the topic publishing FrameWithPose messages
        self.subscription = self.create_subscription(FrameWithPose, 'amps_cpp/pose_estimation/frame_with_pose', self.listener_callback, 10)
        self.get_logger().info(self.subscription.topic_name + ' is subscribed.')
        
        # Initialize CvBridge
        self.bridge = CvBridge()

        self.ground_truth_button_pose = []
        self.ground_truth_button_pose.append({})
        # Load ground truth data
        if self.get_parameter('debugging').value == True:
            try:
                with open('datasets/auto_aligned_dataset/button_pose1/ground_truth.json', 'r') as f:
                    self.ground_truth_button_pose.append(json.load(f))
                with open('datasets/auto_aligned_dataset/button_pose2/ground_truth.json', 'r') as f:
                    self.ground_truth_button_pose.append(json.load(f))
                with open('datasets/auto_aligned_dataset/button_pose3/ground_truth.json', 'r') as f:
                    self.ground_truth_button_pose.append(json.load(f))
                with open('datasets/auto_aligned_dataset/button_pose4/ground_truth.json', 'r') as f:
                    self.ground_truth_button_pose.append(json.load(f))
                with open('datasets/auto_aligned_dataset/button_pose5/ground_truth.json', 'r') as f:
                    self.ground_truth_button_pose.append(json.load(f))
                with open('datasets/auto_aligned_dataset/button_pose6/ground_truth.json', 'r') as f:
                    self.ground_truth_button_pose.append(json.load(f))
                with open('datasets/auto_aligned_dataset/button_pose7/ground_truth.json', 'r') as f:
                    self.ground_truth_button_pose.append(json.load(f))
                with open('datasets/auto_aligned_dataset/button_pose8/ground_truth.json', 'r') as f:
                    self.ground_truth_button_pose.append(json.load(f))
                with open('datasets/auto_aligned_dataset/button_pose9/ground_truth.json', 'r') as f:
                    self.ground_truth_button_pose.append(json.load(f))
                with open('datasets/auto_aligned_dataset/button_pose10/ground_truth.json', 'r') as f:
                    self.ground_truth_button_pose.append(json.load(f))
            except Exception as e:
                self.get_logger().error(f'Error loading ground truth data: {e}')
                self.get_logger().error("Shutting down node.")
                rclpy.shutdown()
                return
            self.publisher_ground_truth = self.create_publisher(CroppedImgDebug, 'amps_python/vision', 10)  
        
        else:
            # Create publishers for transformed depth and color images
            self.publisher_depth = self.create_publisher(Image, 'amps_python/vision/transformed_depth_image', 10)
            self.publisher_color = self.create_publisher(Image, 'amps_python/vision/transformed_color_image', 10)




    def listener_callback(self, sub_msg):
        # Convert ROS Image message to OpenCV image
        depth_image = self.bridge.imgmsg_to_cv2(sub_msg.depth_frame, desired_encoding='passthrough')
        color_image = self.bridge.imgmsg_to_cv2(sub_msg.rgb_frame, desired_encoding='passthrough')
        
        # Process the depth image
        transformed_depth_image, transform_matrix = self.transform_depth(depth_image)
        if transform_matrix is None:
            self.get_logger().warning('Transformation matrix could not be computed. Skipping this frame.')
            return
        transformed_color_image = cv.warpPerspective(color_image, transform_matrix, (transformed_depth_image.shape[1], transformed_depth_image.shape[0]))
        
        # Convert transformed depth to ROS Image message
        transformed_depth_msg = self.bridge.cv2_to_imgmsg(transformed_depth_image, encoding="mono8")

        # Convert transformed color to ROS Image message
        transformed_color_msg = self.bridge.cv2_to_imgmsg(transformed_color_image, encoding="bgr8")
        
        # Publish the transformed image
        if self.get_parameter('debugging').value == True:
            pub_msg = CroppedImgDebug()
            pub_msg.rgb_frame = transformed_color_msg
            pub_msg.depth_frame = transformed_depth_msg
            # Populate ground truth buttons
            ground_truth_buttons = []
            config = sub_msg.button_config
            config = config.split('/')[-1].replace('button_pose', '')  # Extract pose number from string
            num = int(config)
            gt = self.ground_truth_button_pose[num]
            
            # Process each component type in board_state
            board_state = gt.get('board_state', {})
            for component_type, components in board_state.items():
                for component in components:
                    posXY = component.get('posXY', [])
                    if len(posXY) == 2:
                        # posXY format: [[x1, y1], [x2, y2]]
                        top_left = posXY[0]
                        bottom_right = posXY[1]
                        
                        # Transform the bounding box coordinates
                        transformed_bbox = self.transform_bbox(top_left, bottom_right, transform_matrix)
                        
                        button = ClassifiedButton()
                        button.bounding_box = [transformed_bbox[0][0], transformed_bbox[0][1], 
                                             transformed_bbox[1][0], transformed_bbox[1][1]]
                        button.type = component_type
                        ground_truth_buttons.append(button)
            
            pub_msg.buttons = ground_truth_buttons
            self.publisher_ground_truth.publish(pub_msg)
            self.get_logger().info('Published CroppedImgDebug message with transformed images.')
        else:
            self.publisher_depth.publish(transformed_depth_msg)
            self.publisher_color.publish(transformed_color_msg)
        
        self.get_logger().info('Published transformed depth and color image')


    def transform_depth(self, img, show=False):
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
            box = self.order_points(box)  # order points: top-left, top-right, bottom-right, bottom-left
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

    def order_points(self, points):
        box = np.zeros((4,2), dtype="float32")

        sum = points.sum(axis=1)
        box[0] = points[np.argmin(sum)]     # top-left
        box[2] = points[np.argmax(sum)]     # bottom-right

        diff = np.diff(points, axis=1)
        box[1] = points[np.argmin(diff)]  # top-right
        box[3] = points[np.argmax(diff)]  # bottom-left

        return box # return the ordered coordinates like: top-left, top-right, bottom-right, bottom-left

    def transform_bbox(self, point1, point2, transform_matrix):
        """Transform two points from original image to cropped image coordinates.
        
        Args:
            point1: [x1, y1] - first point (e.g., top-left corner)
            point2: [x2, y2] - second point (e.g., bottom-right corner)
            transform_matrix: 3x3 perspective transformation matrix
            
        Returns:
            Two transformed points: [[x1', y1'], [x2', y2']]
        """
        # Create array of the two points
        points = np.array([point1, point2], dtype="float32")
        
        # Reshape for cv.perspectiveTransform (needs shape [1, N, 2])
        points = points.reshape(1, -1, 2)
        
        # Apply perspective transformation
        transformed_points = cv.perspectiveTransform(points, transform_matrix)
        
        # Reshape back and convert to int
        transformed_points = transformed_points[0]
        point1_transformed = [int(transformed_points[0][0]), int(transformed_points[0][1])]
        point2_transformed = [int(transformed_points[1][0]), int(transformed_points[1][1])]
        
        return [point1_transformed, point2_transformed]

def main():
    rclpy.init()
    node = PreprocessingNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
