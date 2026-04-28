from datetime import datetime, timedelta

from sqlalchemy import func, case, distinct

from app.extensions import db
from app.models import Report, Detection, ReportFile


class RealtimeMonitorRepository:
    """
    탐지 현황(독립 페이지) 전용 Repository
    """

    TARGET_RISK_LEVELS = ["주의", "위험", "긴급"]

    # 발표/시연용으로 처리완료까지 지도와 리스트에 유지
    MAP_VISIBLE_STATUSES = ["접수", "확인중", "처리완료"]

    # 기본 조회 기간
    DEFAULT_VISIBLE_DAYS = 180

    @staticmethod
    def count_current_risk_zones(days=DEFAULT_VISIBLE_DAYS):
        since_time = datetime.now() - timedelta(days=days)

        return (
            db.session.query(func.count(distinct(Report.location_text)))
            .filter(Report.deleted_at.is_(None))
            .filter(Report.status.in_(RealtimeMonitorRepository.MAP_VISIBLE_STATUSES))
            .filter(Report.risk_level.in_(RealtimeMonitorRepository.TARGET_RISK_LEVELS))
            .filter(Report.location_text.isnot(None))
            .filter(Report.location_text != "")
            .filter(Report.created_at >= since_time)
            .scalar()
        ) or 0

    @staticmethod
    def count_today_reports():
        today = datetime.now().date()

        return (
            db.session.query(func.count(Report.id))
            .filter(Report.deleted_at.is_(None))
            .filter(func.date(Report.created_at) == today)
            .scalar()
        ) or 0

    @staticmethod
    def count_emergency_last_24h():
        since_time = datetime.now() - timedelta(hours=24)

        return (
            db.session.query(func.count(Report.id))
            .filter(Report.deleted_at.is_(None))
            .filter(Report.risk_level == "긴급")
            .filter(Report.created_at >= since_time)
            .scalar()
        ) or 0

    @staticmethod
    def count_hotspots(days=7, min_count=2):
        since_time = datetime.now() - timedelta(days=days)

        rows = (
            db.session.query(
                Report.location_text,
                func.count(Report.id).label("cnt")
            )
            .filter(Report.deleted_at.is_(None))
            .filter(Report.created_at >= since_time)
            .filter(Report.location_text.isnot(None))
            .filter(Report.location_text != "")
            .group_by(Report.location_text)
            .having(func.count(Report.id) >= min_count)
            .all()
        )

        return len(rows)

    @staticmethod
    def get_summary_data(days=DEFAULT_VISIBLE_DAYS):
        return {
            "current_risk_zones": RealtimeMonitorRepository.count_current_risk_zones(days=days),
            "today_reports": RealtimeMonitorRepository.count_today_reports(),
            "emergency_last_24h": RealtimeMonitorRepository.count_emergency_last_24h(),
            "hotspots": RealtimeMonitorRepository.count_hotspots(days=min(days, 180), min_count=2)
        }

    @staticmethod
    def get_map_points(limit=300, days=DEFAULT_VISIBLE_DAYS):
        since_time = datetime.now() - timedelta(days=days)

        rows = (
            db.session.query(
                Report.id.label("report_id"),
                Report.title.label("title"),
                Report.location_text.label("location_text"),
                Report.latitude.label("latitude"),
                Report.longitude.label("longitude"),
                Report.risk_level.label("risk_level"),
                Report.status.label("status"),
                Report.created_at.label("created_at"),
                Detection.detected_label.label("detected_label"),
                Detection.confidence.label("confidence"),
                Detection.file_id.label("file_id"),
                ReportFile.file_path.label("file_path"),
                ReportFile.file_type.label("file_type")
            )

            .outerjoin(Detection, Detection.report_id == Report.id)
            .outerjoin(ReportFile, ReportFile.id == Detection.file_id)
            .filter(Report.deleted_at.is_(None))
            .filter(Report.status.in_(RealtimeMonitorRepository.MAP_VISIBLE_STATUSES))
            .filter(Report.risk_level.in_(RealtimeMonitorRepository.TARGET_RISK_LEVELS))
            .filter(Report.latitude.isnot(None))
            .filter(Report.longitude.isnot(None))
            .filter(Report.created_at >= since_time)
            .order_by(Report.created_at.desc())
            .limit(limit)
            .all()
        )

        return rows

    @staticmethod
    def get_recent_risk_list(limit=20, days=DEFAULT_VISIBLE_DAYS):
        since_time = datetime.now() - timedelta(days=days)

        risk_order = case(
            (Report.risk_level == "긴급", 3),
            (Report.risk_level == "위험", 2),
            (Report.risk_level == "주의", 1),
            else_=0
        )

        rows = (
            db.session.query(
                Report.id.label("report_id"),
                Report.title.label("title"),
                Report.location_text.label("location_text"),
                Report.risk_level.label("risk_level"),
                Report.status.label("status"),
                Report.created_at.label("created_at"),
                Detection.detected_label.label("detected_label"),
                Detection.confidence.label("confidence")
            )
            .outerjoin(Detection, Detection.report_id == Report.id)
            .filter(Report.deleted_at.is_(None))
            .filter(Report.status.in_(RealtimeMonitorRepository.MAP_VISIBLE_STATUSES))
            .filter(Report.risk_level.in_(RealtimeMonitorRepository.TARGET_RISK_LEVELS))
            .filter(Report.created_at >= since_time)
            .order_by(Report.created_at.desc())
            .limit(limit)
            .all()
        )

        return rows

    @staticmethod
    def get_report_detail(report_id):
        """
        report_id 기준 상세 조회
        - Report 기본 정보
        - Detection 대표 1건
        - ReportFile 대표 1건
        """
        row = (
            db.session.query(
                Report.id.label("report_id"),
                Report.title.label("title"),
                Report.content.label("content"),
                Report.location_text.label("location_text"),
                Report.latitude.label("latitude"),
                Report.longitude.label("longitude"),
                Report.risk_level.label("risk_level"),
                Report.status.label("status"),
                Report.report_type.label("report_type"),
                Report.created_at.label("created_at"),

                Detection.id.label("detection_id"),
                Detection.detected_label.label("detected_label"),
                Detection.confidence.label("confidence"),
                Detection.bbox_x1.label("bbox_x1"),
                Detection.bbox_y1.label("bbox_y1"),
                Detection.bbox_x2.label("bbox_x2"),
                Detection.bbox_y2.label("bbox_y2"),

                ReportFile.id.label("file_id"),
                ReportFile.file_path.label("file_path"),
                ReportFile.file_type.label("file_type"),
                ReportFile.original_name.label("original_name"),
                ReportFile.stored_name.label("stored_name"),
            )
            .outerjoin(Detection, Detection.report_id == Report.id)
            .outerjoin(ReportFile, ReportFile.id == Detection.file_id)
            .filter(Report.deleted_at.is_(None))
            .filter(Report.id == report_id)
            .order_by(Detection.created_at.desc(), ReportFile.uploaded_at.desc())
            .first()
        )

        if row:
            return row

        row_without_detection = (
            db.session.query(
                Report.id.label("report_id"),
                Report.title.label("title"),
                Report.content.label("content"),
                Report.location_text.label("location_text"),
                Report.latitude.label("latitude"),
                Report.longitude.label("longitude"),
                Report.risk_level.label("risk_level"),
                Report.status.label("status"),
                Report.report_type.label("report_type"),
                Report.created_at.label("created_at"),

                ReportFile.id.label("file_id"),
                ReportFile.file_path.label("file_path"),
                ReportFile.file_type.label("file_type"),
                ReportFile.original_name.label("original_name"),
                ReportFile.stored_name.label("stored_name"),
            )
            .outerjoin(ReportFile, ReportFile.report_id == Report.id)
            .filter(Report.deleted_at.is_(None))
            .filter(Report.id == report_id)
            .order_by(ReportFile.uploaded_at.desc())
            .first()
        )

        return row_without_detection