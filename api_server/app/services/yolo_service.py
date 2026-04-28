import os
import requests
from dotenv import load_dotenv

load_dotenv()
AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://localhost:5002")

def detect_image(image_path):
    """
    AI 서버로 이미지 분석을 요청합니다.
    """
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at {image_path}")

        with open(image_path, 'rb') as f:
            files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
            response = requests.post(f"{AI_SERVER_URL}/predict/image", files=files, timeout=30)
            
            if response.status_code != 200:
                print(f"AI Server Error: {response.text}")
                return []
                
            data = response.json()
            return data.get("detections", [])
            
    except requests.exceptions.RequestException as e:
        print(f"AI Server Connection Error (Image): {e}")
        return []
    except Exception as e:
        print(f"detect_image error: {e}")
        return []

def detect_video(video_path):
    """
    AI 서버로 영상 분석을 요청합니다.
    """
    try:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found at {video_path}")

        with open(video_path, 'rb') as f:
            files = {'file': (os.path.basename(video_path), f, 'video/mp4')}
            response = requests.post(f"{AI_SERVER_URL}/predict/video", files=files, timeout=300)
            
            if response.status_code != 200:
                print(f"AI Server Error: {response.text}")
                return []
                
            data = response.json()
            return data.get("detections", [])
            
    except requests.exceptions.RequestException as e:
        print(f"AI Server Connection Error (Video): {e}")
        return []
    except Exception as e:
        print(f"detect_video error: {e}")
        return []