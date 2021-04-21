import cv2


class DetectedObject:
    def __init__(self, name, confidence, yMin, xMin, yMax, xMax):
        self.name = name
        self.confidence = int(confidence *100)
        self.yMin = yMin
        self.xMin = xMin
        self.yMax = yMax
        self.xMax = xMax
        
        self.xCenter = int(xMax - ((xMax - xMin) / 2))
        self.yCenter = int(yMax - ((yMax - yMin) / 2))
        
        
    def drawSelf(self, frame, colors):
        image = frame
        label = '%s: %d%%' % (self.name, self.confidence) # Name and confidence
        labelSize, baseLine = cv2.getTextSize(self.label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2) # Get font size to to scale label
        labelYMin = max(self.yMin, self.labelSize[1] + 10) # Make sure not to draw label too close to top of window
        
        
        cv2.rectangle(image, (self.xMin, self.yMin), (self.xMax, self.yMax), (colors[0], colors[1], colors[2]), 2)
        
        cv2.circle(image, (self.xCenter, self.yCenter), radius = 4, color = (0, 0, 255), thickness = -1)
        
        cv2.rectangle(image, (self.xMin, (labelYMin - labelSize[1]-10)), (self.xMin + labelSize[0], labelYMin), (colors[0], colors[1], colors[2]), cv2.FILLED)
        
        cv2.putText(image, self.label, (self.xMin, self.labelYMin - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        
        return image
            