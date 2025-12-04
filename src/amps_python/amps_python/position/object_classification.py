from amps_python.position.features_extraction import feature_extraction
from amps_cpp.msg import ClassifiedButton, ClassifiedButtonsArray, ProgramState
import cv2 as cv
import rclpy
from rclpy.node import Node
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from cv_bridge import CvBridge
from sensor_msgs.msg import Image 
from std_msgs.msg import Float32MultiArray
import os
from ament_index_python.packages import get_package_share_directory
import time

class ObjectClassificationNode(Node):
    def __init__(self):
        super().__init__('object_classification_node')
        
        #subscribe til segmenteret billede
        self.image_subscription = self.create_subscription(Image, 'segmentation_test_color', self.image_callback, 10)
        #subscribe til roi fra segmentation node
        self.roi_subscription = self.create_subscription(Float32MultiArray, 'segmentation__topic', self.roi_callback, 10)

        #Publicer ClassifiedButtonsArray
        self.classification_publisher = self.create_publisher(ClassifiedButtonsArray, 'object_classification_topic', 10)

        self.programState_sub = self.create_publisher(ProgramState, 'amps/set_program_state', 10)

        #publicer billede med klassificering og bounding boxes for visualisering
        self.image_publisher = self.create_publisher(Image, 'classified_image', 10)

        self.bridge = CvBridge()
        self.current_image = None

        #path to saved data
        folder = os.path.join(
            get_package_share_directory("amps_python"),
            "npy_files"
        )

        #load scaler parameters
        self.mean = np.load(os.path.join(folder, "scaler_mean.npy"))
        self.scale = np.load(os.path.join(folder, "scaler_scale.npy"))

        #load features and labels
        x = np.load(os.path.join(folder, "features.npy"))
        y = np.load(os.path.join(folder, "labels.npy"), allow_pickle=True)


        x_train, X_test, y_train, y_test = train_test_split(
            x, y, test_size=0.3, random_state=0
        )   
        self.knn = KNeighborsClassifier(n_neighbors=3, weights='distance')
        self.knn.fit(x_train, y_train)

        self.get_logger().info("Object Classification Node has been started.")

        self.processed = False
        self.received_image = False
        self.received_roi = False
        self.latest_roi = None

    def set_program_state(self, state: int, state_str: str = ""):
        program_state_msg = ProgramState()
        program_state_msg.state = state
        program_state_msg.state_str = state_str
        self.programState_sub.publish(program_state_msg)


    #fremvisning billede som bruges til debugging
    def image_callback(self, msg):
        #if self.processed:
            #return
        
        self.current_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        self.received_image = True

        if self.received_roi:
            self.process_roi()

    def roi_callback(self, msg):
        #if self.processed:
        #    return
        
        #reshape ROI data fra besked til array af (x1, y1, x2, y2)
        self.latest_roi = np.array(msg.data).reshape(-1, 4)
        self.received_roi = True

        if self.received_image:
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
    
    def process_roi(self):
        #if self.processed:
        #    return
    
        self.get_logger().info("Processing classification.")

        #copyer billedet og henter den seneste ROI
        image = self.current_image.copy()
        rois = self.latest_roi

        #Opret array til at samle alle klassificerede buttons
        buttons_array = ClassifiedButtonsArray()
        buttons_array.buttons = []

        #loop gennem alle ROIs og klassificer dem
        for (x1, y1, x2, y2) in rois:
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            h = y2 - y1
            w = x2 - x1
            
            #håndter store ROIs ved at splitte dem op i mindre sub-ROIs
            #Ellers klassificer den ligesom de andre ROIs bliver og lægger dem i buttons_array
            if h >300 or w >300:
                big_roi = image[y1:y2, x1:x2]
                sub_rois = self.ROI_split(big_roi, count=13)

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
                    if sub_roi.size == 0:
                        continue
                    
                    #Her resizees sub-ROI til 150x150 for feature extraction
                    sub_roi = cv.resize(sub_roi, (150,150))

                    #henter features til sub-ROI
                    features = np.array(feature_extraction(sub_roi))

                    #scale features
                    features = (features - self.mean) / self.scale

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
                    if sub_pred == "circuitBreaker":
                        classifiedButton.type = ClassifiedButton.BREAKER
                    elif sub_pred == "MainSwitch":
                        classifiedButton.type = ClassifiedButton.EMERGENCY_STOP
                    elif sub_pred == "SelectorSwitch":
                        classifiedButton.type = ClassifiedButton.THREE_STATE_SWITCH
                    elif sub_pred == "Plug":
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

            if roi.size == 0:
                continue
            
            #her resizees ROI til 150x150 for feature extraction
            roi = cv.resize(roi, (150,150))

            #henter features til ROI
            features = np.array(feature_extraction(roi))

            #scale features
            features = (features - self.mean) / self.scale

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
            if pred == "circuitBreaker":
                classifiedButton.type = ClassifiedButton.BREAKER
            elif pred == "MainSwitch":
                classifiedButton.type = ClassifiedButton.EMERGENCY_STOP
            elif pred == "SelectorSwitch":
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

        buttons_array.rgb_image = image_msg

        self.get_logger().info(f"Publishing {len(buttons_array.buttons)} buttons")
        self.classification_publisher.publish(buttons_array)        
        
        self.image_publisher.publish(image_msg)
        time.sleep(0.1)

        self.get_logger().info("classification Done")
        # Reset flags to wait for next image+ROI pair

        self.set_program_state(ProgramState.PREPROCESSING_MODE)

        self.received_image = False
        self.received_roi = False 

def main(args=None):
    rclpy.init(args=args)
    node = ObjectClassificationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()