import psycopg2
import base64
import cv2


class Postgresql:
    def __init__(self, login):        
        self.conn = psycopg2.connect(**login)
        self.cur = self.conn.cursor()
        
        try:
            self.cur.execute("""SELECT datname from pg_database""")
            rows = self.cur.fetchall()
            print('Connected to databases:', rows)
        
        except Exception as e:
            raise Excecption("Error connecting to database:", e)  
        
        
    # Write SQL query for adding one object
    def write(self, label, confidence, xposition, yposition, timestamp):
        try:
            self.cur.execute("INSERT INTO picamera (label, confidence, xposition, yposition, timestamp) VALUES (%s, %s, %s, %s, %s)",
                        (label, confidence, xposition, yposition, timestamp))
            print("Success writing to database")
            
        except Exception as e:
            print("error writing to database:", e)
            
            
    # Convert to binary and write image to database
    def writeImage(self, image, timestamp):
        try:
            # Create buffer for encoding image variable to base64 string
            retval, buffer = cv2.imencode('.jpg', image)
            str = base64.b64encode(buffer)
            
            # Convert from base64 string to byte array
            binary = bytearray(str)
            
            self.cur.execute("INSERT INTO images (data, timestamp) VALUES (%s, %s)", (binary, timestamp))
            print("Success writing image to database")
            
        except Exception as e:
            print("error writing image to database:", e)
            

    # Get latest image from database
    def getImage(self):
        try:
            self.cur.execute("SELECT data FROM images ORDER BY timestamp DESC LIMIT 1")
            image_data = self.cur.fetchone()
            print(type(image_data[0]))
            return image_data[0]
            
        except Exception as e:
            print("error getting image from database:", e)
            
    # Commit additions to save    
    def save(self):
        try:
            self.conn.commit()
            print("Success committing to database")
            
        except Exception as e:
            print("error committing to database:", e)
            
    # Close all connections  
    def close(self):
        self.conn.close()
        self.cur.close()
        
            
            
