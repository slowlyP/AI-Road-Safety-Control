import os
import cv2
import uuid
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO, RTDETR
    import torch
except ImportError as e:
    logger.error(f"Error loading AI libraries: {e}")

load_dotenv()
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env")), override=False)

app = FastAPI(title="AI Accident Detection - Inference Server")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "ai", "models")

IMAGE_MODEL_PATH = os.path.join(BASE_DIR, "yolo11n.pt")
VIDEO_MODEL_PATH = os.path.join(BASE_DIR, "yolo11n.pt")

_model_cache = {}

def get_model(model_path: str):
    if model_path in _model_cache:
        return _model_cache[model_path]
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    try:
        # 파일명이나 경로에 rtdetr이 포함되어 있으면 RTDETR로 로드
        if "rtdetr" in model_path.lower():
            model = RTDETR(model_path)
        else:
            model = YOLO(model_path)
        
        _model_cache[model_path] = model
        return model
    except Exception as e:
        logger.error(f"Failed to load model from {model_path}: {e}")
        raise RuntimeError(f"Failed to load model: {str(e)}")

def run_inference(model, source, conf=0.25):
    try:
        results = model.predict(source=source, conf=conf, save=False, verbose=False)
        detections = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0].item())
                conf_val = float(box.conf[0].item())
                xyxy = box.xyxy[0].tolist()
                
                # 라벨 매핑 (YOLO 모델의 names 속성 활용)
                label = r.names.get(cls_id, f"class_{cls_id}")
                
                detections.append({
                    "class_id": cls_id,
                    "label": label,
                    "confidence": round(conf_val, 4),
                    "bbox": [round(v, 2) for v in xyxy]
                })
        return detections
    except RuntimeError as e:
        if "CUDA out of memory" in str(e):
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise HTTPException(status_code=503, detail="GPU memory is full")
        raise e



@app.post("/detect")
@app.post("/predict/image")
async def predict_image(file: UploadFile = File(...)):
    temp_path = os.path.join(os.getenv('TEMP', 'C:/Windows/Temp'), f"{uuid.uuid4()}_{file.filename}")
    try:
        with open(temp_path, "wb") as f:
            f.write(await file.read())
            
        model = get_model(IMAGE_MODEL_PATH)
        detections = run_inference(model, temp_path)
        return {"status": "success", "detections": detections}
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/predict/video")
async def predict_video(file: UploadFile = File(...)):
    temp_path = os.path.join(os.getenv('TEMP', 'C:/Windows/Temp'), f"{uuid.uuid4()}_{file.filename}")
    try:
        with open(temp_path, "wb") as f:
            f.write(await file.read())
            
        model = get_model(VIDEO_MODEL_PATH)
        cap = cv2.VideoCapture(temp_path)
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Cannot open video")
            
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        all_detections = []
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret: break
            frame_count += 1
            if frame_count % 5 != 0: continue
            
            detections = run_inference(model, frame)
            for d in detections:
                d.update({
                    "frame_no": frame_count,
                    "time_sec": round(frame_count / fps, 2),
                    "frame_width": w,
                    "frame_height": h
                })
                all_detections.append(d)
                
        cap.release()
        return {"status": "success", "detections": all_detections}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/compare")
async def compare_models(
    file: UploadFile = File(...), 
    model_version: str = Form(...)
):
    """
    특정 모델 파일을 사용하여 추론 (비교 분석용)
    """
    temp_path = os.path.join(os.getenv('TEMP', 'C:/Windows/Temp'), f"{uuid.uuid4()}_{file.filename}")
    model_path = os.path.join(MODELS_DIR, model_version)
    
    try:
        with open(temp_path, "wb") as f:
            f.write(await file.read())
            
        model = get_model(model_path)
        detections = run_inference(model, temp_path)
        return {"status": "success", "model_version": model_version, "detections": detections}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Model {model_version} not found")
    except Exception as e:
        logger.error(f"Compare error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/health")
def health_check():
    return {"status": "running", "models_loaded": list(_model_cache.keys())}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5002)
