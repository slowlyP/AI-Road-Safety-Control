import os
import cv2
from ultralytics import YOLO, RTDETR

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODEL_PATHS = {
    "image": os.path.join(BASE_DIR, "ai", "models", "best_rtdetr_adamw.pt"),
    "video": os.path.join(BASE_DIR, "ai", "models", "best_video.pt"),
}

_model_cache = {}


def get_model(model_type):
    if model_type in _model_cache:
        return _model_cache[model_type]

    if model_type == "image":
        model = RTDETR(MODEL_PATHS["image"])
    elif model_type == "video":
        model = YOLO(MODEL_PATHS["video"])
    else:
        raise ValueError(f"지원하지 않는 모델 타입입니다: {model_type}")

    _model_cache[model_type] = model
    return model


def parse_results(results, frame_no=None, time_sec=None, frame_width=None, frame_height=None):
    detections = []

    if not results:
        return detections

    for r in results:
        boxes = getattr(r, "boxes", None)
        names = getattr(r, "names", {})

        if boxes is None:
            continue

        xyxy_list = boxes.xyxy.cpu().tolist() if boxes.xyxy is not None else []
        conf_list = boxes.conf.cpu().tolist() if boxes.conf is not None else []
        cls_list = boxes.cls.cpu().tolist() if boxes.cls is not None else []

        for xyxy, conf, cls_idx in zip(xyxy_list, conf_list, cls_list):
            class_id = int(cls_idx)

            detection = {
                "class_id": class_id,
                "label": names.get(class_id, str(class_id)),
                "confidence": round(float(conf), 4),
                "bbox": [round(float(v), 2) for v in xyxy]
            }

            if frame_no is not None:
                detection.update({
                    "frame_no": frame_no,
                    "time_sec": round(time_sec, 2) if time_sec is not None else None,
                    "frame_width": frame_width,
                    "frame_height": frame_height
                })

            detections.append(detection)

    return detections


def detect_image(image_path):
    model = get_model("image")

    results = model.predict(
        source=image_path,
        conf=0.25,
        save=False,
        verbose=False
    )

    return parse_results(results)


def detect_video(video_path, target_fps=5):
    model = get_model("video")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("영상 파일을 열 수 없습니다.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    sample_interval = max(int(round(fps / target_fps)), 1)

    all_detections = []
    frame_no = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_no % sample_interval != 0:
            frame_no += 1
            continue

        time_sec = frame_no / fps

        results = model.predict(
            source=frame,
            conf=0.25,
            imgsz=832,
            save=False,
            verbose=False
        )

        all_detections.extend(
            parse_results(
                results,
                frame_no=frame_no,
                time_sec=time_sec,
                frame_width=frame_width,
                frame_height=frame_height
            )
        )

        frame_no += 1

    cap.release()
    return all_detections