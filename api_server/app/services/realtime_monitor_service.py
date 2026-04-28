from datetime import datetime

from app.repositories.realtime_monitor_repository import RealtimeMonitorRepository


class RealtimeMonitorService:
    """
    탐지 현황 독립 페이지용 서비스
    """

    DEFAULT_DAYS = RealtimeMonitorRepository.DEFAULT_VISIBLE_DAYS

    @staticmethod
    def _safe_float(value, default=0.0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_int(value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _sanitize_days(days, default=DEFAULT_DAYS):
        try:
            value = int(days)
            if value <= 0:
                return default
            return min(value, 365)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _sanitize_limit(limit, default=20, max_limit=500):
        try:
            value = int(limit)
            if value <= 0:
                return default
            return min(value, max_limit)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _format_datetime(dt):
        if not dt:
            return "-"
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _time_ago(dt):
        if not dt:
            return "-"

        now = datetime.now()
        diff = now - dt
        total_seconds = int(diff.total_seconds())

        if total_seconds < 60:
            return f"{total_seconds}초 전"

        minutes = total_seconds // 60
        if minutes < 60:
            return f"{minutes}분 전"

        hours = minutes // 60
        if hours < 24:
            return f"{hours}시간 전"

        days = hours // 24
        return f"{days}일 전"

    @staticmethod
    def _normalize_file_path(file_path):
        if not file_path:
            return ""

        normalized = str(file_path).replace("\\", "/").strip()

        if not normalized.startswith("/"):
            normalized = f"/{normalized}"

        return normalized

    @staticmethod
    def get_summary_cards(days=None):
        days = RealtimeMonitorService._sanitize_days(days)
        return RealtimeMonitorRepository.get_summary_data(days=days)

    @staticmethod
    def get_map_points(limit=300, days=None):
        days = RealtimeMonitorService._sanitize_days(days)
        limit = RealtimeMonitorService._sanitize_limit(limit, default=300, max_limit=1000)

        rows = RealtimeMonitorRepository.get_map_points(limit=limit, days=days)

        result = []
        seen_report_ids = set()

        for row in rows:
            if row.report_id in seen_report_ids:
                continue
            seen_report_ids.add(row.report_id)

            result.append({
                "report_id": row.report_id,
                "title": row.title or "제목 없음",
                "location_text": row.location_text or "위치 정보 없음",
                "latitude": RealtimeMonitorService._safe_float(row.latitude),
                "longitude": RealtimeMonitorService._safe_float(row.longitude),
                "risk_level": row.risk_level or "주의",
                "status": row.status or "-",
                "detected_label": row.detected_label or "미확인",
                "confidence": round(RealtimeMonitorService._safe_float(row.confidence), 2),
                "created_at": RealtimeMonitorService._format_datetime(row.created_at),
                "time_ago": RealtimeMonitorService._time_ago(row.created_at),
                "thumbnail_path": RealtimeMonitorService._normalize_file_path(getattr(row, "file_path", "")),
                "file_type": getattr(row, "file_type", None) or "-"
            })


        return result

    @staticmethod
    def get_recent_risk_list(limit=100, days=None):
        days = RealtimeMonitorService._sanitize_days(days)
        limit = RealtimeMonitorService._sanitize_limit(limit, default=20, max_limit=200)

        rows = RealtimeMonitorRepository.get_recent_risk_list(limit=limit, days=days)
        print([row.risk_level for row in rows])
        result = []
        seen_report_ids = set()

        for row in rows:
            if row.report_id in seen_report_ids:
                continue
            seen_report_ids.add(row.report_id)

            result.append({
                "report_id": row.report_id,
                "title": row.title or "제목 없음",
                "location_text": row.location_text or "위치 정보 없음",
                "risk_level": row.risk_level or "주의",
                "status": row.status or "-",
                "detected_label": row.detected_label or "미확인",
                "confidence": round(RealtimeMonitorService._safe_float(row.confidence), 2),
                "created_at": RealtimeMonitorService._format_datetime(row.created_at),
                "time_ago": RealtimeMonitorService._time_ago(row.created_at)
            })

        return result

    @staticmethod
    def get_report_detail(report_id):
        row = RealtimeMonitorRepository.get_report_detail(report_id)

        if not row:
            return None

        detail = {
            "report_id": getattr(row, "report_id", None),
            "title": getattr(row, "title", None) or "제목 없음",
            "content": getattr(row, "content", None) or "상세 내용 없음",
            "location_text": getattr(row, "location_text", None) or "위치 정보 없음",
            "latitude": RealtimeMonitorService._safe_float(getattr(row, "latitude", None)),
            "longitude": RealtimeMonitorService._safe_float(getattr(row, "longitude", None)),
            "risk_level": getattr(row, "risk_level", None) or "주의",
            "status": getattr(row, "status", None) or "-",
            "report_type": getattr(row, "report_type", None) or "-",
            "created_at": RealtimeMonitorService._format_datetime(getattr(row, "created_at", None)),
            "time_ago": RealtimeMonitorService._time_ago(getattr(row, "created_at", None)),

            "detection_id": getattr(row, "detection_id", None),
            "detected_label": getattr(row, "detected_label", None) or "미확인",
            "confidence": round(
                RealtimeMonitorService._safe_float(getattr(row, "confidence", None)),
                2
            ),
            "bbox": {
                "x1": RealtimeMonitorService._safe_int(getattr(row, "bbox_x1", None)),
                "y1": RealtimeMonitorService._safe_int(getattr(row, "bbox_y1", None)),
                "x2": RealtimeMonitorService._safe_int(getattr(row, "bbox_x2", None)),
                "y2": RealtimeMonitorService._safe_int(getattr(row, "bbox_y2", None)),
            },

            "file_id": getattr(row, "file_id", None),
            "file_path": RealtimeMonitorService._normalize_file_path(getattr(row, "file_path", "")),
            "file_type": getattr(row, "file_type", None) or "-",
            "original_name": getattr(row, "original_name", None) or "-",
            "stored_name": getattr(row, "stored_name", None) or "-",
        }

        return detail