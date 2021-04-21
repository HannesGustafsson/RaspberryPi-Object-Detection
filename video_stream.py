import cv2
from threading import Thread

# Camera class captures images from video feed and uses threading to improve fps by not forcing the rest of the program to wait
class VideoStream:
    def __init__(self,resolution=(640,480)):
        # Initialize piCamera
        self.stream = cv2.VideoCapture(0)
        self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.stream.set(3,resolution[0])
        self.stream.set(4,resolution[1])
            
        # Read first frame from the stream
        (self.grabbed, self.frame) = self.stream.read()

        self.disabled = False

    # Start the thread that reads frames from the video stream
    def start(self):
        Thread(target=self.update,args=()).start()
        return self

    # Loop until thread is stopped
    def update(self):
        while True:
            if self.disabled:
                # Close camera resources
                self.stream.release()
                return

            # Otherwise, grab the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()

    # Returns most recent frame
    def read(self):
        return self.frame

    # Stop camera and thread running camera
    def stop(self):
        self.disabled = True
        
class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)

    def __del__(self):
        self.video.release()        

    def get_frame(self):
        frame = self.video.read()
        jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()