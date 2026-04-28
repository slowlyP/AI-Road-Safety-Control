import os
import cv2
import requests
import numpy as np
from dotenv import load_dotenv

load_dotenv()
load_dotenv("../.env", override=False)

AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://localhost:5002")
predict_url = f"{AI_SERVER_URL}/predict/image"

print(f"Testing connection to: {predict_url}")

# Create a dummy image with a white rectangle to see if it detects anything
img = np.zeros((480, 640, 3), dtype=np.uint8)
cv2.rectangle(img, (100, 100), (300, 300), (255, 255, 255), -1)

try:
    ret, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
    if ret:
        files = {'file': ('frame.jpg', buffer.tobytes(), 'image/jpeg')}
        res = requests.post(predict_url, files=files, timeout=5.0)
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.text}")
    else:
        print("Failed to encode image")
except Exception as e:
    print(f"Error: {e}")
