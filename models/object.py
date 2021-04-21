import cv2


class Object:
    def __init__(self, label, confidence, yMin, xMin, yMax, xMax):
        self.label = label
        self.confidence = int(confidence *100)
        self.yMin = yMin
        self.xMin = xMin
        self.yMax = yMax
        self.xMax = xMax
        
        self.xCenter =
        self.yCenter =