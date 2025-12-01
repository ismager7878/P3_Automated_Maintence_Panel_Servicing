import cv2 as cv
import matplotlib.pyplot as plt
import glob
import numpy as np
import os
import sys
from sklearn.preprocessing import StandardScaler

# Tilføj src directory til Python path
sys.path.insert(0, '/home/sanu/code/P3_Automated_Maintence_Panel_Servicing/src')

from amps_python.amps_python.resources.test import load_image_paths

color_images, depth_images = load_image_paths()
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

real = False

rois_7 = [
    ("breaker", (80, 128, 393, 492)),
    ("breaker", (226,269,397,492)),
    ("breaker", (356,388,394,490)),
    ("breaker", (455,480,394,492)),
    ("red_switch", (216, 342, 740, 869)),
    ("red_switch", ( 67, 190, 732, 872)),
    ("black_switch", (65, 160, 555, 656)),
    ("black_switch", (194, 277, 559, 656)),
    ("black_switch", (313, 395, 557, 656))
]

statemap = {
    1: "top-left",
    2: "top-right",
    3: "bottom-left",
    4: "bottom-right",
    5: "top",
    6: "bottom",
    7: "left",
    8: "right"
}

def feature_extraction_state(img_rgb,img_depth):


    vals = img_depth[250:350, 250:350]
    most_freq_val = np.bincount(vals.flatten()).argmax()

    min_val, max_val = most_freq_val -40, most_freq_val+7
    adjustedImg = ((img_depth.astype(np.float32) - min_val) / (max_val - min_val)) *255
    adjustedImg[adjustedImg < 0] = 0
    adjustedImg[adjustedImg > 255] = 0
    #cv.imshow("Depth Image", adjustedImg.astype(np.uint8))
    cv.imshow("Adjusted Depth Image", adjustedImg.astype(np.uint8))

    adjustedImg = cv.inRange(adjustedImg, 0, 135)
    cv.imshow("Segmented Depth Image", adjustedImg.astype(np.uint8))
    for label, (y1, y2, x1, x2) in rois_7:
        roi = adjustedImg[y1:y2, x1:x2]
       
        number = postion_off_button(roi)
        if(number == None):
            return  
        print(f'{label}: {statemap[number]}')
        cv.imshow(f"ROI - {label}", roi)
        cv.waitKey(0)
    
    #cv.imshow("Adjusted Depth Image", adjustedImg.astype(np.uint8))
    #cv.imshow("RGB Image", img_rgb)
    # for label,(y1, y2, x1, x2) in rois_7:
    #     roi = adjustedImg[y1:y2, x1:x2]
    #     print(label)
    #     postion_off_button(roi)
    cv.waitKey(0)
    cv.destroyAllWindows()
    
 


def postion_off_button(img):
    img = np.asarray(img)
    top_left = 1
    top_right = 2
    bottom_left = 3
    bottom_right = 4
    top = 5
    bottom = 6
    left = 7
    right = 8

    parts = 4

    height, width = img.shape[:2]
    height, width = height/2, width/2

    postion = np.array([[ [None]*3 ]*2]*2)  
    
    treshold = int(np.sum(img == 255))*0.15

    # Calculate white pixel counts in each quadrant
    count = 0
    for i in range(2):
        for j in range(2):
            count +=1
            quadrant = img[int(i*height):int((i+1)*height), int(j*width):int((j+1)*width)]
            postion[i][j][0] = count

            state = 0
            pixel = np.sum(quadrant == 255)
            if(pixel > treshold):
                state = 1
            postion[i][j][1] = state 
            postion[i][j][2] = pixel
    
    print("topleft value", postion[0][0][2])
    print("topright value", postion[0][1][2])
    print("bottomleft value", postion[1][0][2])
    print("bottomright value", postion[1][1][2])    
    # Check position array
    if(postion[0][0][1] == 1):  #top-left
        if(postion[0][1][1] == 1): #top
            return top
        else:
            return top_left
    elif(postion[0][1][1] == 1): #top-right
        if(postion[1][1][1] == 1): #right
            return right
        else:
            return top_right
    elif(postion[1][1][1] == 1): #bottom-right
        if(postion[1][0][1] == 1): #bottom
            return bottom
        else:
            return bottom_right
    elif(postion[1][0][1] == 1): #bottom-left
        if(postion[0][0][1] == 1): #left
            return left
        else:
            return bottom_left




#main function to generate features and labels from dataset images 
#only run when this file is executed directly
if __name__ == "__main__":

    for img_rgb, img_depth in zip(color_images, depth_images):
        feature_extraction_state(img_rgb, img_depth)

    if(real):
        print("Generating features and labels from real-world images...")
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
        "breaker": (355, 405, 420, 530), # 5 fra toppen 
        "black_switch": (200, 310, 590, 690),
        }

        rois_4 = {
        "breaker": (455, 500, 420, 530),
        "black_switch": (85, 180, 590, 690), # 6 fra bunden
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