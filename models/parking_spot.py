import cv2
import numpy as np


def overlaps(parkingspot, objects):
    # Border margin in pixels to make overlap area smaller
    margin = 0
    
    for i in objects:
        if ((i.xCenter < parkingspot.xMax - margin and i.xCenter > parkingspot.xMin + margin)
            and (i.yCenter < parkingspot.yMax - margin and i.yCenter > parkingspot.yMin + margin)):
                return i
                break


class ParkingSpot:
    def __init__(self, name, ymin, xmin, ymax, xmax):
        self.name = name
        self.yMin = ymin
        self.xMin = xmin
        self.yMax = ymax
        self.xMax = xmax
        self.occupied = False
        self.obj = None
        
        
    def occupy(self, obj):
        self.occupied = True
        self.obj = obj
        
        
    def empty(self):
        self.occupied = False
        self.obj = None
         
        
    # Checks if any object which is being tracked is within border
    def check(self, objects):
        ret = overlaps(self, objects)
        if ret is not None:
            if self.occupied == False:
                self.occupy(ret)
        else:
            if self.occupied == True:
                self.empty()
        
        
    def draw_self(self, frame):
        if self.occupied:
            color = 255
        else:
            color = 0
            
        image = frame
        sub_img = image[self.yMin:self.yMax, self.xMin:self.xMax]
        white_rect = np.ones(sub_img.shape, dtype=np.uint8) * color
        res = cv2.addWeighted(sub_img, 0.3, white_rect, 0.5, 1.0)
        
        image[self.yMin:self.yMax, self.xMin:self.xMax] = res
        
        label = self.name # Name
        labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2) # Get font size to to scale label
        labelYMin = max(self.yMin, labelSize[1] + 10) # Make sure not to draw label too close to top of window
        
        
        
        # Draw bounding box around object
        #cv2.rectangle(image, (self.xMin, self.yMin), (self.xMax, self.yMax), (color[0], color[1], color[2]), 2)
        # Draw label background
        #cv2.rectangle(image, (self.xMin, (labelYMin - labelSize[1]-10)), (self.xMin + labelSize[0], labelYMin), (color[0], color[1], color[2]), cv2.FILLED)
        # Draw text on label background
        cv2.putText(image, label, (self.xMin, labelYMin - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)
        
        return image
        
        