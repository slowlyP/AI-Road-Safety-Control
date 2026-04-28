from datetime import datetime

from app.extensions import socketio
from app.repositories.realtime_alert_repository import RealtimeAlertRepository


class RealtimeAlertService:
    """
    실시간 위험 알림 서비스

    역할
    - 확인 대기 / 확인 완료 알림 목록 가공
    - 확인 대기 개수 조회
    - 확인 완료 처리
    - 전체 확인 완료 처리
    - AI 탐지 결과 기반 알림 생성
    - 소켓 실시간 전송
    """

    TARGET_ALERT_LEVELS = ["위험", "긴급"]

    ALERT_MESSAGE_MAP = {
        "위험": "⚠️ 위험 낙하물 탐지! 빠른 조치가 필요합니다.",
        "긴급": "🚨 긴급 낙하물 탐지! 즉시 확인이 필요합니다."
    }

    @staticmethod
    def _normalize_file_path(file_path):
        """
        DB file_path를 브라우저 경로로 정규화

        예:
        static/uploads/a.png  -> /static/uploads/a.png
        /static/uploads/a.png -> /static/uploads/a.png
        """
        if not file_path:
            return ""

        normalized = file_path.replace("\\", "/").strip()

        if not normalized.startswith("/"):
            normalized = f"/{normalized}"

        return normalized

    @staticmethod
    def _serialize_alert_rows(rows):
        """
        Repository 조회 결과를 프론트 전달용 dict 리스트로 변환
        """
        result = []

        for row in rows:
            result.append({
                "alert_id": row.alert_id,
                "report_id": row.report_id,
                "detection_id": row.detection_id,
                "alert_level": row.alert_level,
                "message": row.message,
                "is_read": bool(row.is_read),

                "report_title": row.report_title,
                "location_text": row.location_text or "-",
                "risk_level": row.risk_level or "-",

                "detected_label": row.detected_label or "-",
                "confidence": float(row.confidence) if row.confidence is not None else 0.0,

                "file_type": row.file_type or "-",
                "file_path": RealtimeAlertService._normalize_file_path(row.file_path),
                "original_name": row.original_name or "-",

                "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if row.created_at else "-"
            })

        return result

    @staticmethod
    def get_pending_realtime_alerts(limit=50):
        """
        확인 대기 알림 목록 조회
        """
        rows = RealtimeAlertRepository.find_pending_realtime_alerts(limit=limit)
        return RealtimeAlertService._serialize_alert_rows(rows)

    @staticmethod
    def get_checked_realtime_alerts(limit=50):
        """
        확인 완료 알림 목록 조회
        """
        rows = RealtimeAlertRepository.find_checked_realtime_alerts(limit=limit)
        return RealtimeAlertService._serialize_alert_rows(rows)

    @staticmethod
    def get_pending_count():
        """
        확인 대기 위험/긴급 알림 개수 조회
        """
        return RealtimeAlertRepository.count_pending_alerts()

    @staticmethod
    def mark_as_checked(alert_id):
        """
        특정 알림 확인 완료 처리
        """
        alert = RealtimeAlertRepository.find_alert_by_id(alert_id)

        if not alert:
            return None

        return RealtimeAlertRepository.mark_as_checked(alert)

    @staticmethod
    def mark_all_as_checked():
        """
        전체 위험/긴급 알림 확인 완료 처리
        """
        return RealtimeAlertRepository.mark_all_as_checked()

    @staticmethod
    def create_realtime_alert(report, detection, report_file):
        """
        AI 탐지 결과를 바탕으로 실시간 알림 생성

        흐름
        1. 위험/긴급 여부 확인
        2. alert DB row 생성
        3. 프론트 전달용 payload 생성
        """
        if not report or not detection:
            return None

        if report.risk_level not in RealtimeAlertService.TARGET_ALERT_LEVELS:
            return None

        message = RealtimeAlertService.ALERT_MESSAGE_MAP.get(
            report.risk_level,
            "위험 알림이 발생했습니다."
        )

        new_alert = RealtimeAlertRepository.create_alert(
            report_id=report.id,
            detection_id=detection.id,
            alert_level=report.risk_level,
            message=message
        )

        created_at_text = (
            new_alert.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if getattr(new_alert, "created_at", None)
            else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        payload = {
            "alert_id": new_alert.id,
            "report_id": report.id,
            "detection_id": detection.id,
            "alert_level": report.risk_level,
            "message": message,

            "report_title": report.title,
            "location_text": report.location_text or "-",
            "risk_level": report.risk_level,

            "detected_label": detection.detected_label,
            "confidence": float(detection.confidence)
            if detection.confidence is not None else 0.0,

            "file_type": getattr(report_file, "file_type", "-") if report_file else "-",
            "file_path": RealtimeAlertService._normalize_file_path(
                getattr(report_file, "file_path", "")
            ) if report_file else "",

            "created_at": created_at_text,
            "is_read": False
        }

        return {
            "alert": new_alert,
            "payload": payload
        }

    @staticmethod
    def emit_realtime_alert(payload):
        """
        실시간 알림 소켓 전송
        - 반드시 DB commit 이후 호출
        """
        if not payload:
            return

        socketio.emit(
            "new_realtime_alert",
            payload,
            room="admin_room",
            namespace="/admin/realtime-alert"
        )