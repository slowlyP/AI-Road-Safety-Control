import os
import cv2


def _safe_parse_bbox(det, w, h):
    bbox = det.get("bbox")

    if not bbox or not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return None

    try:
        x1, y1, x2, y2 = bbox

        x1 = max(0, min(w - 1, int(round(float(x1)))))
        y1 = max(0, min(h - 1, int(round(float(y1)))))
        x2 = max(0, min(w - 1, int(round(float(x2)))))
        y2 = max(0, min(h - 1, int(round(float(y2)))))

        # 좌표가 뒤집힌 경우 보정
        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1

        return x1, y1, x2, y2

    except (TypeError, ValueError):
        return None


def draw_bboxes(image_path, detections, save_path):
    """
    이미지 파일 경로를 받아 bbox를 그린 뒤 저장
    """
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"이미지 로드 실패: {image_path}")

    h, w = image.shape[:2]

    for det in detections:
        parsed_bbox = _safe_parse_bbox(det, w, h)
        if parsed_bbox is None:
            continue

        x1, y1, x2, y2 = parsed_bbox

        label = str(det.get("label", "unknown"))

        try:
            conf = float(det.get("confidence", 0))
        except (TypeError, ValueError):
            conf = 0.0

        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

        text = f"{label} {conf:.2f}"
        cv2.putText(
            image,
            text,
            (x1, max(y1 - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2
        )

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    cv2.imwrite(save_path, image)

    return save_path


def draw_bboxes_frame(image, detections, save_path):
    """
    OpenCV 프레임(numpy array)을 받아 bbox를 그린 뒤 저장
    """
    if image is None:
        raise ValueError("프레임 이미지가 없습니다.")

    image = image.copy()
    h, w = image.shape[:2]

    for det in detections:
        parsed_bbox = _safe_parse_bbox(det, w, h)
        if parsed_bbox is None:
            continue

        x1, y1, x2, y2 = parsed_bbox

        label = str(det.get("label", "unknown"))

        try:
            conf = float(det.get("confidence", 0))
        except (TypeError, ValueError):
            conf = 0.0

        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

        text = f"{label} {conf:.2f}"
        cv2.putText(
            image,
            text,
            (x1, max(y1 - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2
        )

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    cv2.imwrite(save_path, image)

    return save_path