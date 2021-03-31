import os
import psycopg2
import json
from datetime import datetime

#datetime.now().strftime("%Y-%m-%d %H:%M:%S")

DIR_NAME = os.path.dirname(__file__)
FILE_NAME = os.path.join(DIR_NAME, 'authentication/details.json')

with open(FILE_NAME, 'r') as f:
    data = f.read()
    print(data)

# parse file
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
        
        
# Commit additions to save    
def save():
    try:
        conn.commit()
        print("Success committing to database")
        
    except Exception as e:
        print("error committing to database:", e)
        
