import cv2 as cv
import matplotlib.pyplot as plt
import glob
import numpy as np
import os
from sklearn.preprocessing import StandardScaler



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


#main function to generate features and labels from dataset images
#only run when this file is executed directly
if __name__ == "__main__":

    img_path = "datasets/test_images_dataset/btn_config_*" 
    image_rgb_files = sorted(glob.glob(os.path.join(img_path, "**/color.png")))
    for file_path in image_rgb_files:
        img = cv.imread(file_path)


    rois_1 = {
    "breaker": (85, 150, 420, 530),
    "black_switch": (540, 660, 590, 690),
    "red_switch": (70, 220, 750, 900)
    }  

    rois_2 = {
    "breaker": (240, 285, 420, 530),
    "black_switch": (430, 530, 590, 690),
    "red_switch": (225, 370, 750, 900)
    }   

    rois_3 = {
    "breaker": (355, 405, 420, 530),
    "black_switch": (200, 310, 590, 690),
    }

    rois_4 = {
    "breaker": (455, 500, 420, 530),
    "black_switch": (85, 180, 590, 690),
    }   

    #saml alle ROIs i en liste
    rois_list = [rois_1, rois_2, rois_3, rois_4]
    X = []   # features
    y = []   # labels

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

    print("TRAIN FEATURES:", X[0:10])
    np.save("features.npy", X)
    np.save("labels.npy", y)


    np.save("scaler_mean.npy", scaler.mean_)
    np.save("scaler_scale.npy", scaler.scale_)


    print("Feature generation DONE.")
    scatter_plot(X, y)