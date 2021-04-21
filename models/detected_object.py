import cv2


# Object class for detected objects containing coordinates and identification properties
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
        
    # Draw bounding box and label  of self on imput image and return it
    def drawSelf(self, frame, colors):
        image = frame
        
        label = '%s: %d%%' % (self.name, self.confidence) # Name and confidence
        labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2) # Get font size to to scale label
        labelYMin = max(self.yMin, labelSize[1] + 10) # Make sure not to draw label too close to top of window
        
        # Draw bounding box around object
        cv2.rectangle(image, (self.xMin, self.yMin), (self.xMax, self.yMax), (colors[0], colors[1], colors[2]), 2)
        # Draw dot at the center of object
        cv2.circle(image, (self.xCenter, self.yCenter), radius = 4, color = (0, 0, 255), thickness = -1)
        # Draw label background
        cv2.rectangle(image, (self.xMin, (labelYMin - labelSize[1]-10)), (self.xMin + labelSize[0], labelYMin), (colors[0], colors[1], colors[2]), cv2.FILLED)
        # Draw text on label background
        cv2.putText(image, label, (self.xMin, labelYMin - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)
        
        
        return image
            