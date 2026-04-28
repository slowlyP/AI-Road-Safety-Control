from datetime import datetime
import os
import uuid
import time
import traceback
import json
import requests

import cv2
from flask import current_app

from app.extensions import db, socketio
from app.models import Report, ReportFile
from app.repositories.ai_compare_repository import AiCompareRepository
from app.utils.draw_bbox import draw_bboxes, draw_bboxes_frame

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

def get_model_inference_from_ai_server(image_path, model_version):
    """
    AI 서버로 특정 모델 버전의 추론을 요청
    """
    url = "http://localhost:5002/compare" 
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {'model_version': model_version}
        response = requests.post(url, files=files, data=data)
    
    if response.status_code != 200:
        print(f"AI Server Error ({model_version}): {response.text}")
        return {"detections": []}
        
    return response.json()

class AdminAICompareService:
    """
    관리자 비교분석 서비스
    - 신고 기준 비교 실행
    - 비교 이력 조회
    - 특정 실행 결과 조회
    """

    MODEL_CONFIGS = [
        {
            "model_name": "YOLOv8",
            "optimizer_name": "SGD",
            "display_name": "YOLOv8 (SGD)",
            "model_version": "best_yolov8_sgd.pt",
        },
        {
            "model_name": "RT-DETR",
            "optimizer_name": "AdamW",
            "display_name": "RT-DETR (AdamW)",
            "model_version": "best_rtdetr_adamw.pt",
        },
        {
            "model_name": "YOLOv8-p2",
            "optimizer_name": None,
            "display_name": "YOLOv8-p2",
            "model_version": "best_yolov8_p2.pt",
        },
    ]

    VIDEO_SAMPLE_FPS = 1

    @staticmethod
    def get_report(report_id):
        return Report.query.get(report_id)

    @staticmethod
    def get_active_file(report_id):
        return (
            ReportFile.query
            .filter_by(report_id=report_id, is_active=1)
            .first()
        )

    @classmethod
    def create_compare_run_only(cls, report_id, requested_by=None):
        report = cls.get_report(report_id)
        if not report:
            raise ValueError("신고 정보를 찾을 수 없습니다.")

        report_file = cls.get_active_file(report_id)
        if not report_file:
            raise ValueError("분석할 활성 파일이 없습니다.")

        source_type = report_file.file_type
        compare_mode = "image" if source_type == "이미지" else "video"

        compare_run = AiCompareRepository.create_compare_run(
            report_id=report.id,
            file_id=report_file.id,
            requested_by=requested_by,
            source_type=source_type,
            compare_mode=compare_mode,
            sample_fps=cls.VIDEO_SAMPLE_FPS if compare_mode == "video" else None,
            total_sampled_frames=None
        )

        AiCompareRepository.update_run_status(compare_run.id, "진행중")
        return compare_run

    @classmethod
    def start_compare_analysis_async(cls, compare_run_id):
        app = current_app._get_current_object()
        socketio.start_background_task(
            cls._run_compare_analysis_background,
            app,
            compare_run_id
        )

    @classmethod
    def _run_compare_analysis_background(cls, app, compare_run_id):
        with app.app_context():
            compare_run = AiCompareRepository.get_run_by_id(compare_run_id)
            if not compare_run:
                return

            report = cls.get_report(compare_run.report_id)
            report_file = ReportFile.query.get(compare_run.file_id)

            if not report or not report_file:
                AiCompareRepository.update_run_status(compare_run_id, "실패")
                return

            success_count = 0
            sampled_frames_for_run = None

            try:
                AiCompareRepository.delete_results_by_run(compare_run_id)

                for model_config in cls.MODEL_CONFIGS:
                    try:
                        result_data = cls.execute_model_analysis(
                            report=report,
                            report_file=report_file,
                            model_config=model_config
                        )

                        if (
                            result_data.get("sampled_frames") is not None
                            and sampled_frames_for_run is None
                        ):
                            sampled_frames_for_run = result_data.get("sampled_frames")

                        safe_result_json = result_data.get("result_json")
                        if safe_result_json is not None:
                            safe_result_json = json.loads(json.dumps(safe_result_json))

                        AiCompareRepository.create_result(
                            compare_run_id=compare_run_id,
                            model_name=result_data["model_name"],
                            optimizer_name=result_data.get("optimizer_name"),
                            model_version=result_data.get("model_version"),
                            total_detections=result_data.get("total_detections", 0),
                            detected_frame_count=result_data.get("detected_frame_count", 0),
                            avg_confidence=result_data.get("avg_confidence"),
                            max_confidence=result_data.get("max_confidence"),
                            processing_time=result_data.get("processing_time"),
                            best_frame_no=result_data.get("best_frame_no"),
                            best_time_sec=result_data.get("best_time_sec"),
                            best_detection_count=result_data.get("best_detection_count"),
                            best_avg_confidence=result_data.get("best_avg_confidence"),
                            best_max_confidence=result_data.get("best_max_confidence"),
                            result_image_path=result_data.get("result_image_path"),
                            result_json=safe_result_json,
                            status=result_data.get("status", "완료"),
                            error_message=result_data.get("error_message")
                        )
                        success_count += 1

                    except Exception as e:
                        error_detail = f"{type(e).__name__}: {e}"
                        print(f"[비교분석 오류] {model_config['model_name']}: {error_detail}")
                        
                        AiCompareRepository.create_result(
                            compare_run_id=compare_run_id,
                            model_name=model_config["model_name"],
                            optimizer_name=model_config.get("optimizer_name"),
                            model_version=model_config.get("model_version"),
                            total_detections=0,
                            status="실패",
                            error_message=error_detail
                        )

                if sampled_frames_for_run is not None:
                    AiCompareRepository.update_run_analysis_info(
                        compare_run_id,
                        sample_fps=cls.VIDEO_SAMPLE_FPS if compare_run.compare_mode == "video" else None,
                        total_sampled_frames=sampled_frames_for_run
                    )

                if success_count == len(cls.MODEL_CONFIGS):
                    AiCompareRepository.update_run_status(compare_run_id, "완료")
                elif success_count > 0:
                    AiCompareRepository.update_run_status(compare_run_id, "부분완료")
                else:
                    AiCompareRepository.update_run_status(compare_run_id, "실패")

            except Exception:
                traceback.print_exc()
                AiCompareRepository.update_run_status(compare_run_id, "실패")

    @classmethod
    def run_compare_analysis(cls, report_id, requested_by=None):
        compare_run = cls.create_compare_run_only(
            report_id=report_id,
            requested_by=requested_by
        )
        cls.start_compare_analysis_async(compare_run.id)
        return AiCompareRepository.get_run_by_id(compare_run.id)

    @classmethod
    def execute_model_analysis(cls, report, report_file, model_config):
        if report_file.file_type == "이미지":
            return cls._analyze_image(report, report_file, model_config)
        elif report_file.file_type == "영상":
            return cls._analyze_video(report, report_file, model_config)

        raise ValueError("지원하지 않는 파일 유형입니다.")

    @classmethod
    def _resolve_paths(cls, report_file):
        # api_server 기준으로 경로 해결
        original_path = os.path.join(BASE_DIR, report_file.file_path)
        if not os.path.exists(original_path):
            # static 폴더 경로 보정
            original_path = os.path.join(BASE_DIR, "app", report_file.file_path)

        if not os.path.exists(original_path):
            raise FileNotFoundError(f"원본 파일이 없습니다: {original_path}")

        return original_path

    @classmethod
    def _build_compare_image_path(cls, model_name):
        filename = f"{model_name}_{uuid.uuid4().hex}.jpg"
        save_path = os.path.join(BASE_DIR, "app", "static", "uploads", "compare", filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        db_path = f"uploads/compare/{filename}"
        return save_path, db_path

    @classmethod
    def _analyze_image(cls, report, report_file, model_config):
        model_name = model_config["model_name"]
        optimizer_name = model_config["optimizer_name"]
        model_version = model_config["model_version"]

        original_path = cls._resolve_paths(report_file)

        start_time = time.time()
        result = get_model_inference_from_ai_server(original_path, model_version)
        detections = result.get('detections', [])
        elapsed_time = round(time.time() - start_time, 4)

        save_path, db_path = cls._build_compare_image_path(model_name)
        draw_bboxes(
            image_path=original_path,
            detections=detections,
            save_path=save_path
        )

        total = len(detections)
        avg_conf = sum(d["confidence"] for d in detections) / total if total > 0 else None
        max_conf = max(d["confidence"] for d in detections) if total > 0 else None

        class_counts = {}
        for d in detections:
            label = d.get("label", "unknown")
            class_counts[label] = class_counts.get(label, 0) + 1

        return {
            "model_name": model_name,
            "optimizer_name": optimizer_name,
            "model_version": model_version,
            "total_detections": total,
            "detected_frame_count": 1 if total > 0 else 0,
            "avg_confidence": round(avg_conf, 4) if avg_conf is not None else None,
            "max_confidence": round(max_conf, 4) if max_conf is not None else None,
            "processing_time": elapsed_time,
            "best_frame_no": 0 if total > 0 else None,
            "best_time_sec": 0.0 if total > 0 else None,
            "best_detection_count": total if total > 0 else None,
            "best_avg_confidence": round(avg_conf, 4) if avg_conf is not None else None,
            "best_max_confidence": round(max_conf, 4) if max_conf is not None else None,
            "result_image_path": db_path,
            "result_json": {
                "class_counts": class_counts,
                "detections": detections
            },
            "status": "완료"
        }

    @classmethod
    def _analyze_video(cls, report, report_file, model_config):
        model_name = model_config["model_name"]
        optimizer_name = model_config["optimizer_name"]
        model_version = model_config["model_version"]

        video_path = cls._resolve_paths(report_file)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"영상 파일을 열 수 없습니다: {video_path}")

        original_fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_interval = max(int(round(original_fps / cls.VIDEO_SAMPLE_FPS)), 1)

        frame_no = 0
        sampled_frames = 0
        detected_frame_count = 0
        total_detections = 0
        sum_conf_all = 0.0
        conf_count_all = 0
        max_conf_all = None
        class_counts = {}
        timeline = []
        best_frame = None

        start_time = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_no % frame_interval != 0:
                frame_no += 1
                continue

            sampled_frames += 1
            
            # 임시 이미지 저장
            temp_img_path = os.path.join(BASE_DIR, "app", "static", "temp_compare_frame.jpg")
            cv2.imwrite(temp_img_path, frame)
            
            # AI 서버에 프레임별 추론 요청
            result = get_model_inference_from_ai_server(temp_img_path, model_version)
            detections = result.get('detections', [])

            detection_count = len(detections)
            time_sec = round(frame_no / original_fps, 2)

            if detection_count > 0:
                detected_frame_count += 1
                total_detections += detection_count
                
                confidences = [d["confidence"] for d in detections]
                avg_conf = sum(confidences) / detection_count
                max_conf = max(confidences)

                sum_conf_all += sum(confidences)
                conf_count_all += len(confidences)
                max_conf_all = max(max_conf_all, max_conf) if max_conf_all is not None else max_conf

                for d in detections:
                    label = d.get("label", "unknown")
                    class_counts[label] = class_counts.get(label, 0) + 1

                current_frame_data = {
                    "frame_no": frame_no,
                    "time_sec": time_sec,
                    "detection_count": detection_count,
                    "avg_confidence": avg_conf,
                    "max_confidence": max_conf,
                    "frame": frame.copy(),
                    "detections": detections
                }

                if best_frame is None or (detection_count > best_frame["detection_count"]):
                    best_frame = current_frame_data

            timeline.append({
                "frame_no": frame_no,
                "time_sec": time_sec,
                "count": detection_count
            })

            frame_no += 1

        cap.release()
        elapsed_time = round(time.time() - start_time, 4)

        result_image_path = None
        best_info = {}
        if best_frame:
            save_path, db_path = cls._build_compare_image_path(model_name)
            draw_bboxes_frame(best_frame["frame"], best_frame["detections"], save_path)
            result_image_path = db_path
            best_info = {
                "best_frame_no": best_frame["frame_no"],
                "best_time_sec": round(best_frame["time_sec"], 2),
                "best_detection_count": best_frame["detection_count"],
                "best_avg_confidence": round(best_frame["avg_confidence"], 4),
                "best_max_confidence": round(best_frame["max_confidence"], 4)
            }

        return {
            "model_name": model_name,
            "optimizer_name": optimizer_name,
            "model_version": model_version,
            "total_detections": total_detections,
            "detected_frame_count": detected_frame_count,
            "avg_confidence": round(sum_conf_all / conf_count_all, 4) if conf_count_all > 0 else None,
            "max_confidence": round(max_conf_all, 4) if max_conf_all is not None else None,
            "processing_time": elapsed_time,
            **best_info,
            "result_image_path": result_image_path,
            "result_json": {
                "class_counts": class_counts,
                "timeline": timeline,
                "sample_fps": cls.VIDEO_SAMPLE_FPS,
                "sampled_frames": sampled_frames
            },
            "status": "완료",
            "sampled_frames": sampled_frames
        }

    @staticmethod
    def get_compare_runs_by_report(report_id):
        return AiCompareRepository.get_runs_by_report(report_id)

    @staticmethod
    def get_compare_run_detail(compare_run_id):
        compare_run = AiCompareRepository.get_run_by_id(compare_run_id)
        if not compare_run:
            return None
        results = AiCompareRepository.get_results_by_run(compare_run_id)
        return {"compare_run": compare_run, "results": results}

    @classmethod
    def get_latest_compare_detail_by_report(cls, report_id):
        latest_run = AiCompareRepository.get_latest_run(report_id)
        if not latest_run:
            return None
        return cls.get_compare_run_detail(latest_run.id)