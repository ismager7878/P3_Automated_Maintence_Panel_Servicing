import string
import numpy as np
import csv
import Button 


        


class Panel:
    def __init__(self,filename,bottomtype,ground_truth,bounding_boxes):
        self.filename = filename
        self.bottomtype = bottomtype
        self.ground_truth = ground_truth
        self.bounding_boxes = bounding_boxes
        self.iou_score = self.csv_to_data(self.bottomtype,self.ground_truth,self.bounding_boxes)



# convert a long streng to data 
    def csv_to_data(self,bottomtype,ground_truth,bounding_boxes):
        bottom_type_list = self.bottom_type(bottomtype)
        ground_truthpostions_list = self.postions(ground_truth)
        bounding_boxes_list = self.postions(bounding_boxes)
        score = self.every_iou(bottom_type_list,ground_truthpostions_list,bounding_boxes_list)
        return score

    # postions number 
    def postions(self,boxes):
        
        list = []
        pos = [None,None,None,None]
        number = ""
        
        index = 0
        for i in boxes:
            if i == "[":
                number = ""
                index = 0
                pos = [None,None,None,None]
            elif i == ",":
                number_float = float(number)
                number_int = int(number_float)
                pos[index] = number_int
                number = ""
                index +=1
            elif i == "]":
                number_float = float(number)
                number_int = int(number_float)
                pos[index] = number_int
                list.append(np.array(pos))
            else:
                number += i
            
        return list
                    

    # postions function but just for "buttomtype" column
    def bottom_type(self,bottomtype):
        list_bottom_type = []
        current_type = ""
        for x,char in enumerate(bottomtype):
            if(not char == ","):
                current_type += char

            if char == "," or x == len(bottomtype)-1:
                # check for special names
                number_of_same = 1
                for name in list_bottom_type:
                    if current_type in name:
                        number_of_same +=1
                current_type = current_type + f"_{str(number_of_same)}"
                        
                list_bottom_type.append(current_type)
                current_type = ""
        return list_bottom_type


    def every_iou(self,type,bbox_get_list,bbox_det_list):

        iou_holder =[ [Button.Button()for _ in range(len(bbox_det_list))] for _ in range(len(bbox_get_list))]
        iou_score = [Button.Button() for _ in range(len(bbox_get_list))]
        diff = (len(bbox_det_list)-len(bbox_get_list))
        # every iou value
        for x, box_gt in  enumerate(bbox_get_list):
            for y, box_det in enumerate(bbox_det_list):
                button = Button.Button()
                button.type = type[x]
                max_iou_value = self.iou_calculator(box_gt,box_det) 
                button.iou = max_iou_value
                button.pos = box_det
                iou_holder[x][y] = button

        # find best iou value for each row
        for x, row in enumerate(iou_holder):
            best_iou = 0.0
            best_button = Button.Button()
            # find best iou in 
            for i, btn in enumerate(row):
                if(i == 0):
                    best_button.type = btn.type
                    iou_score[x] = best_button

                if btn.iou > best_iou:
                    best_iou = btn.iou
                    best_button = btn
                    iou_score[x] = best_button
                

        # samme value set on iou to 0 
        for i in range(len(iou_score)):
            for j in range(i + 1, len(iou_score)):
                # Sammenlign pos arrays
                if np.array_equal(iou_score[i].pos, iou_score[j].pos):
                    if iou_score[i].iou > iou_score[j].iou:
                        iou_score[j].iou = 0.0
                    else:
                        iou_score[i].iou = 0.0

        if diff > 0:
            ekstra = [Button.Button() for _ in range(diff)]
            iou_score.extend(ekstra)
        return iou_score

                    
                
                
                


    count = 0
    def iou_calculator(self, boxA, boxB):
        # boxA and boxB are arrays of [x1, y1, x2, y2] because
        xA = max(boxA[0], boxB[0]) # top-left x
        yA = max(boxA[1], boxB[1]) # top-left y
        xB = min(boxA[2], boxB[2]) # bottom-right x
        yB = min(boxA[3], boxB[3]) # bottom-right y

        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

        iou = interArea / float(boxAArea + boxBArea - interArea)
        return iou
    def show_IOU_scores(self):
        for score in self.iou_score:
            score.show()

    def average_iou(self):
        total_iou = 0.0
        for score in self.iou_score:
            total_iou += score.iou
        average = total_iou / len(self.iou_score)
        return average
    
    def specific_iou(self,button_type):
        """Return the IOU score for a specific button type also ned (_<number>)  ."""
        for score in self.iou_score:
            if score.type == button_type:
                return score.iou
        return None

    def type_iou(self,button_type):

        for score in self.iou_score:
            if score.type == button_type:
                return score.iou
        return None

    def list_types(self,type):
        types = []
        for score in self.iou_score:
            if type in score.type:
                types.append(score)
        return types   





