import cv2

class ParkingSpot:
    def __init__(self, ymin, xmin, ymax, xmax):
        self.yMin = ymin
        self.xMin = xmin
        self.yMax = ymax
        self.xMax = xmax
        self.occupied = False
        self.obj = None
        
    def occupy(self, obj):
        self.obj = obj
        self.occupied = True
        
    def vacate(self):
        self.occupied = False
        self.obj = None
        
    def draw_self(self):
        print('allo')