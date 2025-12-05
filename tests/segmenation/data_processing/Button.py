import numpy as np  
class Button:
    def __init__(self,type = "none",iou = 0.0,pos = np.array([0,0,0,0])):
        self.type = type
        self.iou = iou
        self.pos = pos 
    
    def show(self):
        print("Type: ", self.type)
        print("IOU: ", self.iou)
        print("Position: ", self.pos)