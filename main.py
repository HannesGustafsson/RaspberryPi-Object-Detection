# Import packages
import os
import argparse
import cv2
import numpy as np
import time
import json
from datetime import datetime
from video_stream import VideoStream
from tflite_runtime.interpreter import Interpreter
import postgresql
from models.detected_object import DetectedObject


# Set and parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('--threshold', help='Specify minimum required confidence for an object. Default: 0.5', default=0.5)
parser.add_argument('--objecttypes', help='Specify which object types to keep track of. Default: person car', default='person car 1 2 3 4 5 6 7 8 9')
parser.add_argument('--resolution', help='Specify camera resolution in format WIDTHxHEIGHT. Default: 1280x720', default='1280x720')
args = parser.parse_args()

min_conf_threshold = float(args.threshold)
camera_res = list(map(int, args.resolution.split('x')))
object_types = args.objecttypes.split()

# Remove all elements after 10
if (len(object_types) > 10):
    del object_types[10:]

print('Logging object types: ', object_types)


# Path to working directory
CWD_PATH = os.getcwd()


# Path to model and labelmap used by tflite
MODEL_PATH = os.path.join(CWD_PATH, 'coco_ssd_mobilenet_v1', 'detect.tflite')
LABELS_PATH = os.path.join(CWD_PATH, 'coco_ssd_mobilenet_v1', 'labelmap.txt')
COLORS_PATH = os.path.join(CWD_PATH, 'colors.json')


# Load the label map
with open(LABELS_PATH, 'r') as f:
    labels = [line.strip() for line in f.readlines()]
    
with open(COLORS_PATH, 'r') as f:
    data = f.read()

# Parse file
json_colors = json.loads(data)
colors = json_colors['color']
    

# Load the Tensorflow Lite model.
interpreter = Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()


# Get numbers detailing input requirements for the detection model
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

input_height = input_details[0]['shape'][1]
input_width = input_details[0]['shape'][2]


# Initialize frame rate calculation and timer
fps = 1
timer = round(time.time())
freq = cv2.getTickFrequency()


# Initialize flags and timestamp for sending data to database
object_detected = False
send_data = False
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Initialize video stream
videostream = VideoStream(resolution=(camera_res[0], camera_res[1])).start()
time.sleep(1)



while True:
    # Start frame rate timer
    t1 = cv2.getTickCount()

    # Get snapshot of video stream, convert to correct color space and resize according to input requirements
    frame = videostream.read()
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_resized = cv2.resize(frame_rgb, (input_width, input_height))
    
    input_data = np.expand_dims(frame_resized, axis=0)

    # Perform the object detection by running the model with the image as input
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()

    # Detection results    
    boxes = interpreter.get_tensor(output_details[0]['index'])[0] # Object box cooridinates: boxes[][ymin, xmin, ymax, xmax]
    classes = interpreter.get_tensor(output_details[1]['index'])[0] # Index of object type in labels.txt file: classes[][index]
    scores = interpreter.get_tensor(output_details[2]['index'])[0] # Model confidence in class definition: scores[][float]
            
    # If 10 seconds have passed set send_data flag to True and save current timestamp
    if (round(time.time() > (timer + 10))):
        print('TIMER')
        send_data = True
        timer = round(time.time())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Loop over all detections and draw detection box if confidence is above minimum threshold
    for i in range(len(scores)):
        if ((scores[i] > min_conf_threshold) and (scores[i] <= 1.0)):
            
            # Create new detected object with detection parameters
            obj = DetectedObject(labels[int(classes[i])],
                                      scores[i],
                                      int(max((boxes[i][0] * camera_res[1]), 1)),
                                      int(max((boxes[i][1] * camera_res[0]), 1)),
                                      int(min((boxes[i][2] * camera_res[1]), camera_res[1])),
                                      int(min((boxes[i][3] * camera_res[0]), camera_res[0])))
           
            # Draw object with specific color based on object type
            if (obj.name in object_types):
                for j in range(len(object_types)):
                    if (obj.name == object_types[j]):
                        
                        frame = obj.drawSelf(frame, colors[j])
                        
           # Draw other objects in white  
            else:
                frame = obj.drawSelf(frame, [255, 255, 255])
                
            # If object type is being tracked and 10 seconds have passed
            # Send to database
            if ((obj.name in object_types) and (send_data == True)):
                print(obj.name, obj.confidence, obj.xCenter, obj.yCenter, timestamp)
                object_detected = True
                postgresql.write(obj.name, obj.confidence, obj.xCenter, obj.yCenter, timestamp)
                
        # Rescale and upload screenshot to database every 10 seconds
        if(send_data == True):
            scale_factor = 0.75
            frame_rescaled = cv2.resize(frame, (int(frame.shape[1] * scale_factor), int(frame.shape[0] * scale_factor)))
            postgresql.writeImage(frame_rescaled, timestamp)
            
            postgresql.save()
            object_detected = False
            send_data = False

    # Draw framerate in corner of frame
    cv2.putText(frame,'FPS: {0:.2f}'.format(fps),(30,50),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,0),2,cv2.LINE_AA)

    # All the results have been drawn on the frame, so it's time to display it.
    cv2.imshow('Object detector', frame)

    # Calculate framerate
    t2 = cv2.getTickCount()
    time1 = (t2-t1)/freq
    fps= 1/time1

    # Press 'q' to quit
    if cv2.waitKey(1) == ord('q'):
        break

# Clean up
cv2.destroyAllWindows()
videostream.stop()

# Close connection to the database
postgresql.cur.close()
postgresql.conn.close()