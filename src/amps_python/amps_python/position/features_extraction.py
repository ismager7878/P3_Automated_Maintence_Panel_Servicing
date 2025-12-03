import cv2 as cv
import matplotlib.pyplot as plt
import glob
import numpy as np
import os
from sklearn.preprocessing import StandardScaler
from amps_cpp.msg import ClassifiedButtonArray, ClassifiedButton
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image

class KNN_Node(Node):
    def __init__(self):
        super().__init__("KNN_node")

        self.image_subscription = self.create_subscription(ClassifiedButtonArray, "amps/training_data", KNN_callback,)



#Tager alle RGB channel værdierne og finder deres gennemsnitlige værdi og gør at de har samme gennemsnits værdi
def balance_white(img):
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
def feature_extraction(roi_img):
    roi_img = balance_white(roi_img)
    hsv = cv.cvtColor(roi_img, cv.COLOR_BGR2HSV)
    gray = cv.cvtColor(roi_img, cv.COLOR_BGR2GRAY)
    blur = cv.GaussianBlur(gray, (5,5), 1.2)
    edges = cv.Canny(blur, threshold1=50, threshold2=100)

    contours, _ = cv.findContours(edges, cv.RETR_EXTERNAL, cv .CHAIN_APPROX_SIMPLE)

    edge_density = np.count_nonzero(edges) / edges.size
    num_contours = len(contours)
    std_intensity = np.std(gray)
    mean_intensity = np.mean(gray)
    mean_hue = np.mean(hsv[:,:,0])
    mean_sat = np.mean(hsv[:,:,1])
    mean_value = np.mean(hsv[:,:,2])

    return edge_density, num_contours, std_intensity, mean_intensity, mean_hue, mean_sat, mean_value

#scatter plot for visualizing features
def scatter_plot(X, y):
    colors = {
        "breaker": "blue",
        "black_switch": "black",
        "red_switch": "red"
    }

    plt.rcParams['toolbar'] = 'none'
    fig = plt.figure(figsize=(8,6))
    fig.canvas.manager.set_window_title('')

    for label in np.unique(y):
        idx = np.where(y == label)
        plt.scatter(X[idx, 0], X[idx, 3], label=label, s=20, color=colors[label])

    plt.xlabel("enedge density")
    plt.ylabel("standard deviation of intensity")
    plt.legend()
    plt.grid(True)
    plt.show()


def KNN_callback():
    pass 
      
#main function to generate features and labels from dataset images
#only run when this file is executed directly
if __name__ == "__main__":

    X = []   # features
    y = []   # labels
    rois_list = []  # List to store ROIs for each image
    image_rgb_files = []
    img = None


    for rois in rois_list:
        for label, (y1, y2, x1, x2) in rois.items():

            # FIX: koordinaterne kan være byttet → sorter dem
            y_top    = min(y1, y2)
            y_bottom = max(y1, y2)
            x_left   = min(x1, x2)
            x_right  = max(x1, x2)

            # Tegn boks
            cv.rectangle(img, (x_left, y_top), (x_right, y_bottom), (0, 255, 0), 2)
            cv.putText(img, label, (x_left, y_top - 5),
                    cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # --- VIS BILLEDE ---
    cv.imshow("ROI debug", img)
    cv.waitKey(0)
    cv.destroyAllWindows()

    for rois in rois_list:  # Brug det første billede som eksempel
        for label, (y1, y2, x1, x2) in rois.items():
            cv.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv.putText(img, label, (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2) 


    for img_file in image_rgb_files:
        img = cv.imread(img_file)
        for rois in rois_list:
            for label, (y1, y2, x1, x2) in rois.items():
                roi = img[y1:y2, x1:x2]
                roi = cv.resize(roi, (150,150))
                f1, f2, f3, f4, f5, f6, f7 = feature_extraction(roi)
                X.append([f1, f2, f3, f4, f5, f6, f7])
                y.append(label)

    X = np.array(X)
    y = np.array(y)

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    #print("TRAIN FEATURES:", X[0:10])
    
    #Path hvor KNN og scaler skal gemmes
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(BASE_DIR, "npy_files")

    np.save(os.path.join(folder, "features.npy"), X)
    np.save(os.path.join(folder, "labels.npy"), y)


    np.save(os.path.join(folder, "scaler_mean.npy"), scaler.mean_)
    np.save(os.path.join(folder, "scaler_scale.npy"), scaler.scale_)


    print("Feature generation DONE.")