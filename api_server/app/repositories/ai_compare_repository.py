from datetime import datetime

import json
from app.extensions import db
from app.models import AiCompareRun, AiCompareResult


class AiCompareRepository:

    @staticmethod
    def create_compare_run(
        report_id,
        file_id,
        requested_by,
        source_type,
        compare_mode="video",
        sample_fps=None,
        total_sampled_frames=None
    ):
        run = AiCompareRun(
            report_id=report_id,
            file_id=file_id,
            requested_by=requested_by,
            source_type=source_type,
            compare_mode=compare_mode,
            sample_fps=sample_fps,
            total_sampled_frames=total_sampled_frames,
            status="대기"
        )
        db.session.add(run)
        db.session.commit()
        return run

    @staticmethod
    def update_run_status(run_id, status):
        run = AiCompareRun.query.get(run_id)
        if not run:
            return None

        run.status = status

        if status == "진행중" and run.started_at is None:
            run.started_at = datetime.now()

        if status in ["완료", "실패"]:
            run.finished_at = datetime.now()

        db.session.commit()
        return run

    @staticmethod
    def update_run_analysis_info(run_id, sample_fps=None, total_sampled_frames=None):
        run = AiCompareRun.query.get(run_id)
        if not run:
            return None

        if sample_fps is not None:
            run.sample_fps = sample_fps

        if total_sampled_frames is not None:
            run.total_sampled_frames = total_sampled_frames

        db.session.commit()
        return run

    @staticmethod
    def get_run_by_id(run_id):
        return AiCompareRun.query.get(run_id)

    @staticmethod
    def get_runs_by_report(report_id):
        return (
            AiCompareRun.query
            .filter_by(report_id=report_id)
            .order_by(AiCompareRun.created_at.desc())
            .all()
        )

    @staticmethod
    def get_latest_run(report_id):
        return (
            AiCompareRun.query
            .filter_by(report_id=report_id)
            .order_by(AiCompareRun.created_at.desc())
            .first()
        )

    @staticmethod
    def create_result(
        compare_run_id,
        model_name,
        optimizer_name=None,
        model_version=None,
        total_detections=0,
        detected_frame_count=0,
        avg_confidence=None,
        max_confidence=None,
        processing_time=None,
        best_frame_no=None,
        best_time_sec=None,
        best_detection_count=None,
        best_avg_confidence=None,
        best_max_confidence=None,
        result_image_path=None,
        result_json=None,
        status="완료",
        error_message=None
    ):
        result = AiCompareResult(
            compare_run_id=compare_run_id,
            model_name=model_name,
            optimizer_name=optimizer_name,
            model_version=model_version,
            total_detections=total_detections,
            detected_frame_count=detected_frame_count,
            avg_confidence=avg_confidence,
            max_confidence=max_confidence,
            processing_time=processing_time,
            best_frame_no=best_frame_no,
            best_time_sec=best_time_sec,
            best_detection_count=best_detection_count,
            best_avg_confidence=best_avg_confidence,
            best_max_confidence=best_max_confidence,
            result_image_path=result_image_path,
            result_json=result_json,
            status=status,
            error_message=error_message
        )
        db.session.add(result)
        db.session.commit()
        return result

    @staticmethod
    def get_results_by_run(compare_run_id):
        return (
            AiCompareResult.query
            .filter_by(compare_run_id=compare_run_id)
            .order_by(AiCompareResult.id.asc())
            .all()
        )

    @staticmethod
    def delete_results_by_run(compare_run_id):
        AiCompareResult.query.filter_by(compare_run_id=compare_run_id).delete()
        db.session.commit()