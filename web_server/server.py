from flask import Flask, render_template, Response
from PIL import Image
import os, sys
import base64
import io
import cv2

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
import postgresql

    
app = Flask(__name__)

@app.route("/")
def hello():
    image_mv = postgresql.getImage()
    image = bytes(image_mv)
    print(image)
    #img = Image.frombytes('RGBA', (640, 360), image)
    #img.save("foo.png")
    
    
    
    im = Image.open("image.jpg")
    data = io.BytesIO()
    im.save(data, "JPEG")
    encoded_img_data = base64.b64encode(image)
    
    message = "Hello, World"
    return render_template("index.html", img_data=encoded_img_data.decode('utf-8'))

if __name__ == '__main__':

    app.run(host='0.0.0.0', debug=False)