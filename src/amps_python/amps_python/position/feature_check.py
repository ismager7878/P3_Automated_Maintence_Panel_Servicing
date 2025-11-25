import cv2 as cv
import glob
import os
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from amps_python.amps_python.position.features_extraction import feature_extraction, balance_white


#Preprocessing the image, so make objects of interest stand out more clearly
def preprocess_image(img):
    img = balance_white(img)
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

    mask_red = cv.inRange(hsv, (0, 120, 70), (10, 255, 255)) + cv.inRange(hsv, (170, 120, 70), (180, 255, 255))
    mask_black = cv.inRange(hsv, (0, 0, 0), (180, 255, 50))
    mask_blue = cv.inRange(hsv, (90, 100, 70), (130, 255, 255))


    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    _, mask_dark = cv.threshold(gray, 60, 255, cv.THRESH_BINARY_INV)
    mask_black = cv.bitwise_and(mask_black, mask_dark)

    # Morfologiske operationer – fjerner små pletter og støj
    kernel = np.ones((5, 5), np.uint8)
    mask_red = cv.morphologyEx(mask_red, cv.MORPH_OPEN, kernel)
    mask_red = cv.morphologyEx(mask_red, cv.MORPH_CLOSE, kernel)

    mask_black = cv.morphologyEx(mask_black, cv.MORPH_OPEN, kernel)
    mask_black = cv.morphologyEx(mask_black, cv.MORPH_CLOSE, kernel)

    mask_blue = cv.morphologyEx(mask_blue, cv.MORPH_OPEN, kernel)
    mask_blue = cv.morphologyEx(mask_blue, cv.MORPH_CLOSE, kernel)


    mask = cv.bitwise_or(mask_red, mask_black)
    mask = cv.bitwise_or(mask, mask_blue)

    # Sørg for at masken er uint8
    mask = mask.astype(np.uint8)

    result = cv.bitwise_and(img, img, mask=mask)
    mask = cv.bitwise_or(mask_red, cv.bitwise_or(mask_black, mask_blue))
    #result = cv.bitwise_and(img, img, mask=mask)
        
    return result, mask

#find potential candidate objects in the image
def find_candidate_objects(img):
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    blur = cv.GaussianBlur(gray, (7,7), 1.4)

    v = np.median(blur)
    edges = cv.Canny(blur, int(max(0, 1.4 * v)), int(min(255, 1.3 * v)))
    kernel = np.ones((3, 3), np.uint8)
    edges = cv.morphologyEx(edges, cv.MORPH_CLOSE, kernel)

    contours, _ = cv.findContours(edges, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    filtered_contours = []
    #thresholds for area and aspect ratio
    for cnt in contours:
        area = cv.contourArea(cnt)
        if 175 < area < 120000:
            x, y, w, h = cv.boundingRect(cnt)
            aspect_ratio = w / float(h)
            if 0.3 < aspect_ratio < 2.0:
                filtered_contours.append(cnt)
        
    return filtered_contours

#localize and classify objects using trained KNN
def localize_and_classify(img, contours, knn):
    centers = []
    for cnt in contours:
        x, y, w, h = cv.boundingRect(cnt)
        roi = img[y:y+h, x:x+w]
        f1, f2, f3, f4, f5, f6, f7 = feature_extraction(roi)
        pred = str(knn.predict([[f1, f2, f3, f4, f5, f6, f7]])[0])

        M = cv.moments(cnt)
        if M["m00"] != 0:
            cx = int(M["m10"]/M["m00"])
            cy = int(M["m01"]/M["m00"])
            centers.append((cx, cy, pred))
            cv.circle(img, (cx, cy), 5, (0,0,255), -1)
            cv.putText(img, pred, (cx+10, cy), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
    return img, centers


#load dataset features and labels
X = np.load("features.npy")
y = np.load("labels.npy", allow_pickle=True)

x_train, x_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=0
)

knn = KNeighborsClassifier(n_neighbors=3, weights='distance')
knn.fit(x_train, y_train)

#image file path to test
file_path = "datasets/test_images_dataset/btn_config_1/rosbag2_2025_10_30-14_13_08_0/color.png"


img = cv.imread(file_path)
filtered_img, mask = preprocess_image(img)
#finder blobs in the preprocessed image
num_labels, labels, stats, centroids = cv.connectedComponentsWithStats(mask)

output = img.copy()
detected = []

#loop through all detected blobs, filtrering small ones out, extract features, scale them and classify using KNN
for i in range(1, num_labels):
    x, y, w, h, area = stats[i]

    # filtrer små objekter fra:
    if area < 300 or w <= 0 or h <= 0:
        continue

    roi = img[y:y+h, x:x+w]

    if roi.size == 0:
        continue
    
    roi = cv.resize(roi, (150,150))

    f = np.array(feature_extraction(roi))

    # --- SCALER ---
    mean = np.load("scaler_mean.npy")
    scale = np.load("scaler_scale.npy")
    f = (f - mean) / scale


    pred = knn.predict([f])[0]

    cx, cy = map(int, centroids[i])

    cv.circle(output, (cx, cy), 5, (0,0,255), -1)
    cv.putText(output, pred, (cx+10, cy), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

    detected.append((cx, cy, pred))

print("Detected:", detected)

cv.imshow("Result", output)
cv.waitKey(0)
cv.destroyAllWindows()
