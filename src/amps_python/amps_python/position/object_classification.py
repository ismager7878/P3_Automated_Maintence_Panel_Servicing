from amps_cpp.msg import ClassifiedButton, ClassifiedButtonsArray, ProgramState
import cv2 as cv
import rclpy
from rclpy.node import Node
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from cv_bridge import CvBridge
from sensor_msgs.msg import Image 
from std_msgs.msg import Float32MultiArray, UInt16MultiArray
import os
from ament_index_python.packages import get_package_share_directory
import time


def find_workspace_root(start_path):
    current = start_path
    while current != "/":
        if "src" in os.listdir(current) and "install" in os.listdir(current):
            return current
        current = os.path.abspath(os.path.join(current, ".."))
    raise RuntimeError("Workspace root not found")

class ObjectClassificationNode(Node):
    def __init__(self):
        super().__init__('object_classification_node')

        self.declare_parameter('button_state', 'false')
        
        #subscribe til segmenteret billede
        self.image_subscription = self.create_subscription(Image, 'amps/vision/transformed_color_image', self.image_callback, 10)
        #subscribe til depth billede
        self.depth_subscription = self.create_subscription(Image, 'amps/vision/transformed_depth_image', self.depth_callback, 10)
        #subscribe til roi fra segmentation node
        self.roi_subscription = self.create_subscription(Float32MultiArray, 'amps/vision/bounding_boxes', self.roi_callback, 10)

        self.exclusion_subscription = self.create_subscription(UInt16MultiArray, 'amps/validation/feature_exclusions', self.exclusion_callback, 10)

        #Publicer ClassifiedButtonsArray
        self.classification_publisher = self.create_publisher(ClassifiedButtonsArray, '/amps/vision/type_classification', 10)
        self.programState_sub = self.create_publisher(ProgramState, 'amps/set_program_state', 10)

        #publicer billede med klassificering og bounding boxes for visualisering
        self.image_publisher = self.create_publisher(Image, 'amps/images/type_classification', 10)

        self.bridge = CvBridge()
        self.current_image = None
        self.current_depth = None

        self.current_exclusions = []

        #path to saved data
        BASE_DIR = os.path.dirname(os.path.realpath(__file__))
        WORKSPACE_ROOT = find_workspace_root(BASE_DIR)
        folder = os.path.join(WORKSPACE_ROOT, "datasets", "KNN_scaler_data")

        #load scaler parameters
        self.mean = np.load(os.path.join(folder, "scaler_mean.npy"))
        self.scale = np.load(os.path.join(folder, "scaler_scale.npy"))

        #load features and labels
        self.x = np.load(os.path.join(folder, "features.npy"))
        self.y = np.load(os.path.join(folder, "labels.npy"), allow_pickle=True)

  
        self.knn = KNeighborsClassifier(n_neighbors=5, weights='distance')
        self.knn.fit(self.x, self.y)

        self.get_logger().info("Object Classification Node has been started.")

        self.processed = False
        self.received_image = False
        self.received_depth = False
        self.received_roi = False
        self.latest_roi = None

    def set_program_state(self, state: int, state_str: str = ""):
        program_state_msg = ProgramState()
        program_state_msg.state = state
        program_state_msg.state_str = state_str
        self.programState_sub.publish(program_state_msg)

    def exclusion_callback(self, msg):
        self.current_exclusions = list(msg.data)
        self.get_logger().info(f"Updated exclusion zones: {self.current_exclusions}")
        
        # Retrain KNN with excluded features
        if len(self.current_exclusions) > 0:
            self.x_reduced = np.delete(self.x, self.current_exclusions, axis=1)
            self.knn = KNeighborsClassifier(n_neighbors=5, weights='distance')
            self.knn.fit(self.x_reduced, self.y)
            self.get_logger().info(f"Retrained KNN with shape: {self.x_reduced.shape}")
        else:
            # Reset to original if no exclusions
            self.knn = KNeighborsClassifier(n_neighbors=5, weights='distance')
            self.knn.fit(self.x, self.y)

    #fremvisning billede som bruges til debugging
    def image_callback(self, msg):
        #if self.processed:
            #return
        
        self.current_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        self.received_image = True

        if self.received_roi and self.received_depth:
            self.process_roi()

    def depth_callback(self, msg):
        #if self.processed:
            #return
        
        self.current_depth = self.bridge.imgmsg_to_cv2(msg, desired_encoding='8UC1')
        self.received_depth = True

        if self.received_roi and self.received_image:
            self.process_roi()

    def roi_callback(self, msg):
        #if self.processed:
        #    return
        
        #reshape ROI data fra besked til array af (x1, y1, x2, y2)
        self.latest_roi = np.array(msg.data).reshape(-1, 4)
        self.received_roi = True

        if self.received_image and self.received_depth:
            self.process_roi()

    #splitter den store ROI med breakswitchs i mindre del-ROIs
    #Det område at fast 13 knapper, der er count=13 som standard
    def ROI_split(self, image_roi, count=13):
        h, w = image_roi.shape[:2]

        slice_height = h // count

        sub_rois = []

        #lav de mindre ROIs, ved at skære billedet horisontalt op
        for i in range(count):
            y1 = i * slice_height
            y2 = (i + 1) * slice_height if i < count - 1 else h
            x1 = 0
            x2 = w
            sub_rois.append((x1, y1, x2, y2))

        return sub_rois
    
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
        all_features = np.concatenate([scalar_features, histogram.flatten()])
        
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
    
    def process_roi(self):
        #if self.processed:
        #    return
    
        self.get_logger().info("Processing classification.")

        #copyer billedet og henter den seneste ROI
        image = self.current_image.copy()
        depth_image = self.current_depth.copy()

        rois = self.latest_roi

        #Opret array til at samle alle klassificerede buttons
        buttons_array = ClassifiedButtonsArray()
        buttons_array.buttons = []
        
        # Set the RGB and depth images in the message
        buttons_array.rgb_image = self.bridge.cv2_to_imgmsg(self.current_image, encoding='bgr8')
        # Use the actual depth image received
        buttons_array.depth_image = self.bridge.cv2_to_imgmsg(self.current_depth, encoding='mono8')

        #loop gennem alle ROIs og klassificer dem
        for (x1, y1, x2, y2) in rois:
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            h = y2 - y1
            w = x2 - x1
            
            #håndter store ROIs ved at splitte dem op i mindre sub-ROIs
            #Ellers klassificer den ligesom de andre ROIs bliver og lægger dem i buttons_array
            if h >300 or w >300:
                big_roi = image[y1:y2, x1:x2]
                big_droi = depth_image[y1:y2, x1:x2]
                sub_rois = self.ROI_split(big_roi, count=13)
                sub_drois = self.ROI_split(big_droi, count=13)

                for (sx1, sy1, sx2, sy2) in sub_rois:
                    sx1_global = x1 + sx1
                    sy1_global = y1 + sy1
                    sx2_global = x1 + sx2
                    sy2_global = y1 + sy2

                    sw = sx2 - sx1
                    sh = sy2 - sy1

                    if sh <=0 or sw <=0:
                        continue

                    sub_roi = image[sy1_global:sy2_global, sx1_global:sx2_global]
                    sub_droi = depth_image[sy1_global:sy2_global, sx1_global:sx2_global]

                    if sub_roi.size == 0:
                        continue
                    
                    #Her resizees sub-ROI til 150x150 for feature extraction
                    sub_roi = cv.resize(sub_roi, (150,150))
                    sub_droi = cv.resize(sub_droi, (150,150))

                    #henter features til sub-ROI
                    features = np.array(self.feature_extraction(sub_roi, sub_droi))

                    #scale features
                    features = (features - self.mean) / self.scale

                     # Apply exclusions to features if any exist
                    if len(self.current_exclusions) > 0:
                        features = np.delete(features, self.current_exclusions)

                    #giver classificering
                    sub_pred = self.knn.predict([features])[0]

                    #vis sub-ROI med klassificering på billedet til debugging
                    cv.rectangle(image, (sx1_global, sy1_global), (sx2_global, sy2_global), (255, 0, 0), 2)
                    cv.putText(image, sub_pred, (sx1_global, sy1_global - 10), cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

                    #midten af knappen
                    scx = sx1_global + sw // 2
                    scy = sy1_global + sh // 2
                    
                    #Her gemmer vi den klassificerede button i classifiedButton beskeden
                    classifiedButton = ClassifiedButton()
                    if sub_pred == "BREAKER":
                        classifiedButton.type = ClassifiedButton.BREAKER
                    elif sub_pred == "EMERGENCY_STOP":
                        classifiedButton.type = ClassifiedButton.EMERGENCY_STOP
                    elif sub_pred == "THREE_STATE_SWITCH":
                        classifiedButton.type = ClassifiedButton.THREE_STATE_SWITCH
                    elif sub_pred == "PLUG":
                        classifiedButton.type = ClassifiedButton.PLUG
                    else:
                        classifiedButton.type = ClassifiedButton.UNKNOWN
                    
                    #gem bounding box og dot position i beskeden
                    classifiedButton.bounding_box = [int(sx1_global), int(sy1_global), int(sx2_global), int(sy2_global)]
                    classifiedButton.dot_position = [int(scx), int(scy)]
                    # Tilføj button til array
                    buttons_array.buttons.append(classifiedButton)
                continue
            
            #tjek for gyldig ROI størrelse
            if h <=0 or w <=0:
                continue

            roi = image[y1:y2, x1:x2]
            droi = depth_image[y1:y2, x1:x2]

            if roi.size == 0:
                continue
            
            #her resizees ROI til 150x150 for feature extraction
            roi = cv.resize(roi, (150,150))
            droi = cv.resize(droi, (150,150))

            #henter features til ROI
            features = np.array(self.feature_extraction(roi, droi))

            #scale features
            features = (features - self.mean) / self.scale

            # Apply exclusions to features if any exist
            if len(self.current_exclusions) > 0:
                features = np.delete(features, self.current_exclusions)

            
           
            #giver classificering
            pred = self.knn.predict([features])[0]

            #viser ROI med klassificering på billedet til debugging
            cv.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv.putText(image, pred, (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            

            #midten af knappen
            cx = x1 + w // 2
            cy = y1 + h // 2
            
            #Her gemmer vi den klassificerede button i classifiedButton beskeden
            classifiedButton = ClassifiedButton()
            if pred == "BREAKER":
                classifiedButton.type = ClassifiedButton.BREAKER
            elif pred == "EMERGENCY_STOP":
                classifiedButton.type = ClassifiedButton.EMERGENCY_STOP
            elif pred == "THREE_STATE_SWITCH":
                classifiedButton.type = ClassifiedButton.THREE_STATE_SWITCH
            elif pred == "Plug":
                classifiedButton.type = ClassifiedButton.PLUG
            else:
                classifiedButton.type = ClassifiedButton.UNKNOWN

            #gem bounding box og dot position i beskeden
            classifiedButton.bounding_box = [int(x1), int(y1), int(x2), int(y2)]
            classifiedButton.dot_position = [int(cx), int(cy)]

            # Tilføj button til array
            buttons_array.buttons.append(classifiedButton)

        #publicer alle klassificerede buttons og billedet med visualisering
        image_msg = self.bridge.cv2_to_imgmsg(image, encoding='bgr8')

        self.get_logger().info(f"Publishing {len(buttons_array.buttons)} buttons")
        self.classification_publisher.publish(buttons_array)        
        
        self.image_publisher.publish(image_msg)
        time.sleep(0.1)

        self.get_logger().info("classification Done")
        # Reset flags to wait for next image+ROI pair

        if(self.get_parameter('button_state').get_parameter_value().string_value == 'false'):
            self.set_program_state(ProgramState.PREPROCESSING_MODE, "Button State Detection Mode")
        ##self.set_program_state(ProgramState.PREPROCESSING_MODE)

        self.received_image = False
        self.received_depth = False
        self.received_roi = False

def main(args=None):
    rclpy.init(args=args)
    node = ObjectClassificationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()