import os
import psycopg2
import json
import base64
import cv2


CWD_PATH = os.path.dirname(__file__)
FILE_PATH = os.path.join(CWD_PATH, 'authentication/details.json')

with open(FILE_PATH, 'r') as f:
    data = f.read()
    print(data)

# Parse file
obj = json.loads(data)


try:
    conn = psycopg2.connect(**obj)
    cur = conn.cursor()
    cur.execute("""SELECT datname from pg_database""")
    rows = cur.fetchall()
    print('Connected to databases:', rows)
    
except Exception as e:
    print("Error connecting to database:", e)
    
    
# Write SQL query for adding one object
def write(label, confidence, xposition, yposition, timestamp):
    try:
        cur.execute("INSERT INTO picamera (label, confidence, xposition, yposition, timestamp) VALUES (%s, %s, %s, %s, %s)",
                    (label, confidence, xposition, yposition, timestamp))
        print("Success writing to database")
        
    except Exception as e:
        print("error writing to database:", e)
        
        
# Convert to binary and write image to database
def writeImage(image, timestamp):
    try:
        retval, buffer = cv2.imencode('.jpg', image)
        str = base64.b64encode(buffer)
        binary = bytearray(str)
        print(binary)
        cur.execute("INSERT INTO images (data, timestamp) VALUES (%s, %s)", (binary, timestamp))
        print("Success writing image to database")
        #cur.execute("INSERT INTO images(data) VALUES (%s)", (binary,))
        
    except Exception as e:
        print("error writing image to database:", e)
        

# Get latest image from database
def getImage():
    try:
        cur.execute("SELECT data FROM images ORDER BY timestamp DESC LIMIT 1")
        image_data = cur.fetchone()
        print(type(image_data[0]))
        return image_data[0]
        
    except Exception as e:
        print("error getting image from database:", e)
        
# Commit additions to save    
def save():
    try:
        conn.commit()
        print("Success committing to database")
        
    except Exception as e:
        print("error committing to database:", e)
        
