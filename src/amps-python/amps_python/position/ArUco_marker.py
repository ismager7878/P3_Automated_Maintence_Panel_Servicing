import cv2 as cv
import cv2.aruco as aruco
import numpy as np
import os

def loadImage(image_path):
    image = cv.imread(image_path)
    if image is None:
        print("---------------------------")
        print("Error in image path")
        print("---------------------------")
    return image


image = loadImage("/home/petur/Documents/Github/P3_Automated_Maintence_Panel_Servicing/src/amps-python/amps-python/data/board2.jpg")

#Alle aruco dictionaries i opencv:
#-------------------------------------------------------------------
arucoDict4x4 = aruco.getPredefinedDictionary(aruco.DICT_4X4_1000)
arucoDict5x5 = aruco.getPredefinedDictionary(aruco.DICT_5X5_1000)
arucoDict6x6 = aruco.getPredefinedDictionary(aruco.DICT_6X6_1000)
arucoDict7x7 = aruco.getPredefinedDictionary(aruco.DICT_7X7_1000)
#-------------------------------------------------------------------

libStorage = [arucoDict4x4, arucoDict5x5, arucoDict6x6, arucoDict7x7] 

def dict_finder(image_path):
    #converte image into grayscale before aruco detection

    gray = cv.cvtColor(image_path, cv.COLOR_BGR2GRAY)

    for i in range(len(libStorage)):
        parameters = aruco.DetectorParameters()
        detector = aruco.ArucoDetector(libStorage[i], parameters)
        corner, ids, rejected = detector.detectMarkers(gray)
        
        if ids is not None and len(ids) > 2 and i == 0:
            print("4x4 library is a match")    
            return libStorage[i]
        
        if ids is not None and len(ids) > 2 and i == 1:
            print("5x5 library is a match")
            return libStorage[i]
        
        if ids is not None and len(ids) > 2 and i == 3:
            print("6x6 library is a match")
            return libStorage[i]
        
        if ids is not None and len(ids) > 2 and i == 4:
            print("7x7 library is a match")
            return libStorage[i]
    
    print("No matches found")

        #for debugging ->
"""
        if ids is not None and len(ids) > 2:
            print("---------------------------------------")
            print(f"library: {i}")
            print("---------------------------------------")
            print(f"Corner: {corner} id: {ids}")
            print("---------------------------------------")


            aruco.drawDetectedMarkers(image_path, corner, ids)

            #aruco.drawDetectedMarkers(img_resize, rejected, borderColor=(0,0,255))

            img_resize = cv.resize(image_path, (768,1024))
            cv.imshow("Detected Markers",img_resize)
            cv.waitKey(0)
            cv.destroyAllWindows()
            return libStorage[i]
        
        else:
            print("---------------------------------------")
            print(f"{i} not a match")
            print("---------------------------------------")  
"""      
dict_finder(image)

def generate_ArUco():
    # Define the dictionary we want to use
    aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_5X5_1000)

    # Generate a marker
    marker1_id = 0
    marker2_id = 1
    marker3_id = 2
    marker_size = 300  # Size in pixels (generic pixel size)
    marker_image1 = cv.aruco.generateImageMarker(aruco_dict, marker1_id, marker_size)
    marker_image2 = cv.aruco.generateImageMarker(aruco_dict, marker2_id, marker_size)
    marker_image3 = cv.aruco.generateImageMarker(aruco_dict, marker3_id, marker_size)

    # define folder placement
    mappe = r"C:\Users\hamme\OneDrive\Uni\ROB\Semester_3\Projekt\ArUco-project-markers"

    # Vælger mappe og hvad for et billede der skal sættes i mappen
    sti1 = os.path.join(mappe, "marker_image1.jpg")
    sti2 = os.path.join(mappe, "marker_image2.jpg")
    sti3 = os.path.join(mappe, "marker_image3.jpg")

    # Gem billede i mappen
    gem1 = cv.imwrite(sti1, marker_image1)
    gem2 = cv.imwrite(sti2, marker_image2)
    gem3 = cv.imwrite(sti3, marker_image3)

    if gem1 and gem2 and gem3:
        print("Saved")
    else:
        print("Something went wrong")


    cv.imshow("marker 1",marker_image1)
    cv.imshow("marker 2",marker_image2)
    cv.imshow("marker 3",marker_image3)
    cv.waitKey(0)
    cv.destroyAllWindows()



