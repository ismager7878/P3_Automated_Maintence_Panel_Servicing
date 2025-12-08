import cv2 as cv
import matplotlib.pyplot as plt
import glob
import numpy as np
import os
from sklearn.preprocessing import StandardScaler
from amps_cpp.msg import ClassifiedButtonsArray, ClassifiedButton
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

class KNN_Node(Node):
    def __init__(self):
        super().__init__("KNN_node")

        self.image_subscription = self.create_subscription(ClassifiedButtonsArray, "amps/training_data", self.KNN_callback, 10)

        self.image_publisher = self.create_publisher(Image, 'debugging_image', 10)

        self.bridge = CvBridge()
        self.X = []
        self.y = []



    #Tager alle RGB channel værdierne og finder deres gennemsnitlige værdi og gør at de har samme gennemsnits værdi
    def balance_white(self, img):
        result = img.copy().astype(np.float32)
        avg_b = np.mean(result[:,:,0])
        avg_g = np.mean(result[:,:,1])
        avg_r = np.mean(result[:,:,2])
        avg_gray = (avg_b + avg_g + avg_r) / 3
        result[:,:,0] *= avg_gray / (avg_b + 1e-5)
        result[:,:,1] *= avg_gray / (avg_g + 1e-5)
        result[:,:,2] *= avg_gray / (avg_r + 1e-5)
        return np.clip(result, 0, 255).astype(np.uint8)

    #Henter feature af edges density, edge contours, standard deviation of intensity, mean intensity, mean hue, mean saturation, mean value
    def feature_extraction(self, roi_img, roi_depth):
        #roi_img = self.balance_white(roi_img)
        hsv = cv.cvtColor(roi_img, cv.COLOR_BGR2HSV)
        gray = cv.cvtColor(roi_img, cv.COLOR_BGR2GRAY)
        blur = cv.GaussianBlur(gray, (5,5), 1.2)
        edges = cv.Canny(blur, threshold1=50, threshold2=100)

        #contours, _ = cv.findContours(edges, cv.RETR_EXTERNAL, cv .CHAIN_APPROX_SIMPLE)

        depth_top = self.top_pixels_coutour(roi_depth, p=.05)

        topShape = cv.minAreaRect(depth_top)
        box = cv.boxPoints(topShape)
        box = np.int0(box)

        box_height = np.linalg.norm(box[0] - box[1])
        box_width = np.linalg.norm(box[1] - box[2])

        if(box_width == 0):
            box_width = 1

        HW_ratio = box_height / box_width

        area = cv.contourArea(depth_top)

        histogram = cv.calcHist([hsv], [0], None, [8], [0, 256])

        min_value = hsv[:,:,0].min()
        max_value = hsv[:,:,0].max()

        #edge_density = np.count_nonzero(edges) / edges.size
        #num_contours = len(contours)
        std_intensity = np.std(gray)
        std_depth = np.std(roi_depth)
        #mean_intensity = np.mean(gray)
        #mean_hue = np.mean(hsv[:,:,0])
        min_hue = np.min(hsv[:,:,0])
        max_hue = np.max(hsv[:,:,0])
        mean_sat = np.mean(hsv[:,:,1])
        #mean_value = np.mean(hsv[:,:,2])

        # Concatenate scalar features with histogram
        scalar_features = np.array([std_depth, std_intensity, min_hue, max_hue, area, HW_ratio, min_value, max_value])
        all_features = np.concatenate([scalar_features], histogram.flatten())
        
        return all_features
    
    def top_pixels_coutour(self, depth_img, p=0.1):
        # Flatten the depth image and get the indices of the top n smallest values (closest points)
        flat_depth = depth_img.flatten()
        n_top = int(len(flat_depth) * p)
        top_n_indices = np.argpartition(flat_depth, n_top)[:n_top]

        # Create a binary mask for the top n pixels
        mask = np.zeros_like(flat_depth, dtype=bool)
        mask[top_n_indices] = True
        mask = mask.reshape(depth_img.shape)

        # Find contours in the mask
        contours, _ = cv.findContours(mask.astype(np.uint8), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        sorted_contours = sorted(contours, key=cv.contourArea, reverse=True)
        
        main_contour = sorted_contours[0]

        return main_contour
    
    def KNN_callback(self, msg):  
        img = self.bridge.imgmsg_to_cv2(msg.rgb_image, "bgr8")
        depth_img = self.bridge.imgmsg_to_cv2(msg.depth_image, "32FC1")

        debug_img = img.copy()
        color = (0, 255, 0)

        for button in msg.buttons:
            if button.type == 1:
                label = "BREAKER"
            elif button.type == 2:
                label = "THREE_STATE_SWITCH"
            elif button.type == 3:
                label = "EMERGENCY_STOP"
            elif button.type == 4:
                label = "PLUG"
                continue  # Skip plugs for now
            else:
                label = "UNKNOWN"

            x1, y1, x2, y2 = button.bounding_box

            roi = img[y1:y2, x1:x2]
            dRoi = depth_img[y1:y2, x1:x2]

            if roi.size == 0:
                continue
            

            cv.rectangle(debug_img, (x1, y1), (x2, y2), color, 2)
            cv.putText(debug_img, f"T:{button.type}",
                   (x1, y1 - 4),
                   cv.FONT_HERSHEY_SIMPLEX,
                   0.5, color, 1)
            

            roi = cv.resize(roi, (150,150))
            dRoi = cv.resize(dRoi, (150,150))
            features = self.feature_extraction(roi, dRoi)

            self.X.append(features)
            self.y.append(label)

        debug_msg = self.bridge.cv2_to_imgmsg(debug_img, encoding="bgr8")
        self.image_publisher.publish(debug_msg)
        self.get_logger().info(f"Received {len(msg.buttons)} buttons. Total samples: {len(self.X)}")

    def find_workspace_root(self,start_path):
        current = start_path
        while current != "/":
            if "src" in os.listdir(current) and "install" in os.listdir(current):
                return current
            current = os.path.abspath(os.path.join(current, ".."))
        raise RuntimeError("Workspace root not found")


    def save_model(self):
        X = np.array(self.X, dtype=np.float16)
        y = np.array(self.y, dtype=str)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Find path relative to *src folder*, ikke install folder.
        BASE_DIR = os.path.dirname(os.path.realpath(__file__))
        WORKSPACE_ROOT = self.find_workspace_root(BASE_DIR)

        
        folder = os.path.join(WORKSPACE_ROOT, "datasets", "KNN_scaler_data")
        os.makedirs(folder, exist_ok=True)

        np.save(os.path.join(folder, "features.npy"), X_scaled)
        np.save(os.path.join(folder, "labels.npy"), y)
        np.save(os.path.join(folder, "scaler_mean.npy"), scaler.mean_)
        np.save(os.path.join(folder, "scaler_scale.npy"), scaler.scale_)

        self.get_logger().info(f"Training complete. Saved {len(self.X)} samples to {folder}")

        print("Feature generation DONE.")


def main(args=None):
    rclpy.init(args=args)

    node = KNN_Node()   
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutdown requested (KeyboardInterrupt). Saving data...")
    finally:
        # Gem data før vi lukker helt ned
        try:
            node.save_model()
        except Exception as e:
            node.get_logger().error(f"Error saving model: {e}")
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()