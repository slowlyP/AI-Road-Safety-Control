import os
import cv2
import time
import logging
import threading
import requests
from flask import Flask, Response, jsonify
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env")), override=False)

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# 환경변수에서 카메라 소스 로드
CAM_SOURCES = {
    0: os.getenv("CAM_0_SOURCE", 0),
    1: os.getenv("CAM_1_SOURCE"),
    2: os.getenv("CAM_2_SOURCE"),
    3: os.getenv("CAM_3_SOURCE")
}

# 문자열 "0" 등 처리
for k, v in CAM_SOURCES.items():
    if isinstance(v, str) and v.isdigit():
        CAM_SOURCES[k] = int(v)

# 연결 재시도 등을 위한 클래스
class CameraStreamer:
    def __init__(self, cam_id, source):
        self.cam_id = cam_id
        self.source = source
        self.cap = None
        self.latest_frame = None
        self.latest_detections = []
        self.running = True
        self.connect()
        
        # Start AI inference thread
        self.ai_thread = threading.Thread(target=self.run_ai_inference, daemon=True)
        self.ai_thread.start()

    def run_ai_inference(self):
        AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://localhost:5002")
        predict_url = f"{AI_SERVER_URL}/predict/image"
        
        while self.running:
            if self.latest_frame is not None:
                try:
                    # Resize or encode the frame to avoid sending massive data over HTTP
                    # For performance, we can just encode directly
                    ret, buffer = cv2.imencode('.jpg', self.latest_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                    if ret:
                        files = {'file': ('frame.jpg', buffer.tobytes(), 'image/jpeg')}
                        res = requests.post(predict_url, files=files, timeout=2.0)
                        if res.status_code == 200:
                            data = res.json()
                            if data.get("status") == "success":
                                self.latest_detections = data.get("detections", [])
                except Exception as e:
                    # AI 서버 연결 실패 등의 에러는 무시하여 스트리밍에 영향을 주지 않음
                    pass
            time.sleep(0.3)  # Approx 3 FPS inference

    def connect(self):
        if self.source is None:
            return
        
        try:
            if self.cam_id != 0:
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
                self.cap = cv2.VideoCapture(self.source)
            else:
                self.cap = cv2.VideoCapture(self.source)
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 30)

            if not self.cap.isOpened():
                app.logger.error(f"카메라 {self.cam_id} ({self.source}) 연결 실패")
            else:
                app.logger.info(f"카메라 {self.cam_id} 연결 성공")
        except Exception as e:
            app.logger.error(f"카메라 {self.cam_id} 초기화 중 예외 발생: {e}")

    def get_frame(self):
        if self.cap is None or not self.cap.isOpened():
            self.connect() # 연결 끊김시 재시도
            time.sleep(2)  # 재시도 지연
            if self.cap is None or not self.cap.isOpened():
                return None
            
        success, frame = self.cap.read()
        if not success:
            app.logger.warning(f"카메라 {self.cam_id} 프레임 읽기 실패. 재연결 시도 중...")
            self.cap.release()
            return None
        
        self.latest_frame = frame.copy()
        return frame

    def release(self):
        self.running = False
        if self.cap:
            self.cap.release()

# 카메라 스트리머 전역 관리
streamers = {}
for cam_id, source in CAM_SOURCES.items():
    if source is not None:
        streamers[cam_id] = CameraStreamer(cam_id, source)

def draw_bboxes(frame, detections):
    if frame is None or not detections:
        return frame
        
    h, w = frame.shape[:2]
    for det in detections:
        bbox = det.get("bbox")
        if not bbox or len(bbox) != 4: continue
        
        # AI 서버에서 정규화된 좌표(0~1)를 보내는 경우 처리
        # 모든 좌표가 1.1 이하이면 정규화된 좌표로 간주하여 화면 크기에 맞게 곱함
        is_normalized = all(v <= 1.1 for v in bbox)
        
        if is_normalized:
            x1 = int(bbox[0] * w)
            y1 = int(bbox[1] * h)
            x2 = int(bbox[2] * w)
            y2 = int(bbox[3] * h)
        else:
            x1, y1, x2, y2 = [int(v) for v in bbox]

        label = str(det.get("label", "unknown"))
        try:
            conf = float(det.get("confidence", 0))
        except:
            conf = 0.0
            
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        text = f"{label} {conf:.2f}"
        cv2.putText(frame, text, (x1, max(y1 - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
    return frame

def generate_frames(cam_id):
    streamer = streamers.get(cam_id)
    if streamer is None:
        return
    
    # 예외 상황(에러) 처리를 위해 더미 프레임 생성(검은 화면) 준비 가능
    while True:
        try:
            frame = streamer.get_frame()
            if frame is None:
                # 에러 또는 연결 끊김 시
                time.sleep(1)
                continue
            
            # 여기서 AI 분석 결과(바운딩 박스)를 그립니다
            frame = draw_bboxes(frame, streamer.latest_detections)
            
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
                
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        except Exception as e:
            app.logger.error(f"스트리밍 중 예외 발생 (cam_id: {cam_id}): {e}")
            time.sleep(1)

@app.route('/stream/<int:cam_id>')
def stream(cam_id):
    if cam_id not in streamers:
        return jsonify({"error": "존재하지 않는 카메라 ID"}), 404
        
    return Response(generate_frames(cam_id), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/health')
def health_check():
    status = {}
    for cam_id, streamer in streamers.items():
        status[cam_id] = "OK" if streamer.cap and streamer.cap.isOpened() else "ERROR"
    return jsonify({"status": "running", "cameras": status})

if __name__ == '__main__':
    port = int(os.getenv("CAM_SERVER_PORT", 5003))
    try:
        app.run(host='0.0.0.0', port=port, threaded=True)
    finally:
        for s in streamers.values():
            s.release()
