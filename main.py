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
from postgresql import Postgresql
from models.detected_object import DetectedObject
from models.parking_spot import ParkingSpot


# Set and parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('--threshold', help = 'Specify minimum required confidence for an object. Default: 0.5', default = 0.5)
parser.add_argument('--objecttypes', help =' Specify which object types to keep track of. Default: person car motorcycle truck', default = 'person car truck motorcycle')
parser.add_argument('--resolution', help = 'Specify camera resolution in format WIDTHxHEIGHT. Default: 1280x720', default = '1280x720')
parser.add_argument('--interval', help = 'Specify minimum DB transmission interval. Default: 10', default = 10)
args = parser.parse_args()

MIN_CONF_THRESHOLD = float(args.threshold) # Minimum confidence level for detection
CAMERA_RES = list(map(int, args.resolution.split('x'))) # Array containing camera resolution
OBJECT_TYPES = args.objecttypes.split() # Array containing tracked object types
TRANSMISSION_INTERVAL = int(args.interval) # Minimum numbers of seconds between database inserts

# Limit number of tracked object types to 10
if (len(OBJECT_TYPES) > 10):
    del OBJECT_TYPES[10:]

print('Logging object types:', OBJECT_TYPES)
print('DB transmission interval:', TRANSMISSION_INTERVAL)


# Path to working directory
CWD_PATH = os.getcwd()


# Path to model and labelmap used by tflite
MODEL_PATH = os.path.join(CWD_PATH, 'coco_ssd_mobilenet_v1', 'detect.tflite')
LABELS_PATH = os.path.join(CWD_PATH, 'coco_ssd_mobilenet_v1', 'labelmap.txt')
COLORS_PATH = os.path.join(CWD_PATH, 'colors.json')
LOGIN_PATH = os.path.join(CWD_PATH, 'authentication/details.json')


# Load the label map
with open(LABELS_PATH, 'r') as f:
    labels = [line.strip() for line in f.readlines()]
    f.close()
        
# Open file with color codes to display different object types as different colors, based on order in OBJECT_TYPES list
with open(COLORS_PATH, 'r') as f:
    data = f.read()
    json_colors = json.loads(data)
    colors = json_colors['color']
    f.close()

# Open file with login details
with open(LOGIN_PATH, 'r') as f:
    try:
        data = f.read()
        json_login = json.loads(data)
        print(json_login)
        print(f'Connecting to PostgreSQL DB: "%s" with user: "%s"' % (json_login['dbname'], json_login['user']))
        
        # Set up database connection
        postgres = Postgresql(json_login)
    except Exception as e:
        print("database connection error:", e)
    finally:
        f.close()


# Load the Tensorflow Lite model.
interpreter = Interpreter(model_path = MODEL_PATH)
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
videostream = VideoStream(resolution=(CAMERA_RES[0], CAMERA_RES[1])).start()
time.sleep(1)

# Create list of parking spots
parkingspots = [
    ParkingSpot("PS1", 100, 100, 300, 500),
    ParkingSpot("PS2", 350, 100, 550, 500)]


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
    
    tracked_objects = 0
    untracked_objects = 0
    
    data_sent = False
            
    # If 10 seconds have passed set send_data flag to True and save current timestamp
    if (round(time.time() > (timer + TRANSMISSION_INTERVAL))):
        print('TIMER')
        send_data = True
        timer = round(time.time())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Loop over all detections and draw detection box if confidence is above minimum threshold
    objects_list = []
    for i in range(len(scores)):
        if ((scores[i] > MIN_CONF_THRESHOLD) and (scores[i] <= 1.0)):
            
            # Create new detected object with detection parameters
            obj = DetectedObject(labels[int(classes[i])],
                                      scores[i],
                                      int(max((boxes[i][0] * CAMERA_RES[1]), 1)),
                                      int(max((boxes[i][1] * CAMERA_RES[0]), 1)),
                                      int(min((boxes[i][2] * CAMERA_RES[1]), CAMERA_RES[1])),
                                      int(min((boxes[i][3] * CAMERA_RES[0]), CAMERA_RES[0])))
           
            # Draw object with specific color based on object type index in OBJECT_TYPES list              
            if (obj.name in OBJECT_TYPES):
                frame = obj.draw_self(frame, colors[OBJECT_TYPES.index(obj.name)])
                objects_list.append(obj) 
                tracked_objects += 1
                
                # Insert into database as soon as a tracked object is detected if 10 seconds have passed since last insert
                # After that, insert every 10 seconds as long as one or more tracked objects are in frame
                if(send_data == True):
                    print(obj.name, obj.confidence, obj.xCenter, obj.yCenter, timestamp)
                    postgres.write(obj.name, obj.confidence, obj.xCenter, obj.yCenter, timestamp)
                    data_sent = True
                        
           # Draw other objects in white  
            else:
                frame = obj.draw_self(frame, [255, 255, 255])
                untracked_objects += 1
     
    send_data = False # Reset send_data flag
    # Check all parking spots for vacance and draw boxes
    for i in parkingspots:
        i.check(objects_list)
        frame = i.draw_self(frame)
                
    # Draw framerate in corner of frame (cv2.putText does not support "\n", thus a for loop is needed)
    menu_text = [f'Press Esc to exit', f'Fps: {fps:.2f}',
                 f'Tracked objects: {tracked_objects}',
                 f'Untracked objects: {untracked_objects}']
    
    spacing = cv2.getTextSize('X', cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)
    
    for i in range(len(menu_text)):
        cv2.putText(frame, menu_text[i], (20, 30 + (i * (spacing[0][1] + 5))), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)       


    # Rescale and upload screenshot to database every 10 seconds
    if(data_sent == True):
        scale_factor = 0.75
        frame_rescaled = cv2.resize(frame, (int(frame.shape[1] * scale_factor), int(frame.shape[0] * scale_factor)))
        postgres.writeImage(frame_rescaled, timestamp)
        
        postgres.save()
        data_sent = False
        
    # Display image on screen
    cv2.imshow('Camera Feed', frame)


    # Calculate framerate
    t2 = cv2.getTickCount()
    time1 = (t2-t1)/freq
    fps= 1/time1


    # Press 'q' to quit
    if cv2.waitKey(1) == 27:
        break


# Clean up
cv2.destroyAllWindows()
videostream.stop()

# Close connection to the database
postgres.close()