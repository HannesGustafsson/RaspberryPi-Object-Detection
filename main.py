# Import packages
import os
import argparse
import cv2
import numpy as np
import time
import video_stream
from tflite_runtime.interpreter import Interpreter
import postgresql


# Set and parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('--threshold', help='Specify minimum required confidence for an object. Default: 0.5', default=0.5)
parser.add_argument('--objecttypes', help='Specify which object types to keep track of. Default: person car', default='person car')
parser.add_argument('--resolution', help='Specify camera resolution in format WIDTHxHEIGHT. Default: 1280x720', default='1280x720')
args = parser.parse_args()

min_conf_threshold = float(args.threshold)
object_types = args.objecttypes.split()
camera_res = list(map(int, args.resolution.split('x')))

print('Logging object types: ', object_types)

MODEL_PATHNAME = 'coco_ssd_mobilenet_v1'
GRAPH_NAME = 'detect.tflite'
LABELMAP_NAME = 'labelmap.txt'


# Path to working directory
CWD_PATH = os.getcwd()


# Path to model and labelmap used by tflite
MODEL_PATH = os.path.join(CWD_PATH,MODEL_PATHNAME,GRAPH_NAME)
LABELS_PATH = os.path.join(CWD_PATH,MODEL_PATHNAME,LABELMAP_NAME)


# Load the label map
with open(LABELS_PATH, 'r') as f:
    labels = [line.strip() for line in f.readlines()]
    

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


# Initialize video stream
videostream = video_stream.VideoStream(resolution=(camera_res[0], camera_res[1])).start()
time.sleep(1)


while True:
    # Start frame rate timer
    t1 = cv2.getTickCount()

    # Get snapshot of video stream, convert to color space and resize according to input requirements
    frame = videostream.read()
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_resized = cv2.resize(frame_rgb, (input_width, input_height))
    
    input_data = np.expand_dims(frame_resized, axis=0)

    # Perform the actual detection by running the model with the image as input
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()

    # Retrieve detection results    
    boxes = interpreter.get_tensor(output_details[0]['index'])[0] # Bounding box coordinates of detected objects
    classes = interpreter.get_tensor(output_details[1]['index'])[0] # Class index of detected objects
    scores = interpreter.get_tensor(output_details[2]['index'])[0] # Confidence of detected objects
    
    # Check timer and send data
    if (round(time.time() > (timer + 10))):
        for i in range(len(scores)):
            if ((scores[i] > min_conf_threshold) and (scores[i] <= 1.0)):
                for j in object_types:
                    if (labels[int(classes[i])] == j):
                        print(j)
                        print(timer)
            
        timer = round(time.time())

    # Loop over all detections and draw detection box if confidence is above minimum threshold
    for i in range(len(scores)):
        if ((scores[i] > min_conf_threshold) and (scores[i] <= 1.0)):

            # Get bounding box coordinates and draw box
            # Interpreter can return coordinates that are outside of image dimensions, need to force them to be within image using max() and min()
            ymin = int(max(1,(boxes[i][0] * camera_res[1])))
            xmin = int(max(1,(boxes[i][1] * camera_res[0])))
            ymax = int(min(camera_res[1],(boxes[i][2] * camera_res[1])))
            xmax = int(min(camera_res[0],(boxes[i][3] * camera_res[0])))
            
            cv2.rectangle(frame, (xmin,ymin), (xmax,ymax), (10, 255, 0), 2)

            # Draw label
            object_name = labels[int(classes[i])] # Look up object name from "labels" array using class index
            label = '%s: %d%%' % (object_name, int(scores[i]*100)) # Example: 'person: 72%'
            labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2) # Get font size
            label_ymin = max(ymin, labelSize[1] + 10) # Make sure not to draw label too close to top of window
            cv2.rectangle(frame, (xmin, label_ymin-labelSize[1]-10), (xmin+labelSize[0], label_ymin+baseLine-10), (255, 255, 255), cv2.FILLED) # Draw white box to put label text in
            cv2.putText(frame, label, (xmin, label_ymin-7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2) # Draw label text
            
            #if(object_name == "person"):
               #postgresql.write()

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