from datetime import datetime, timedelta

from sqlalchemy import func, case

from app.extensions import db
from app.models.report_model import Report
from app.models.detection_model import Detection


class AdminRegionAnalysisRepository:
    """
    관리자 위험 지역 분석 Repository
    """

    DEFAULT_DAYS = 30
    TARGET_RISK_LEVELS = ["주의", "위험", "긴급"]
    TARGET_STATUSES = ["접수", "확인중", "처리완료"]

    @staticmethod
    def _get_since_time(days):
        return datetime.now() - timedelta(days=days)

    @staticmethod
    def get_region_points(days=30, detected_label=None, risk_level=None):
        since_time = AdminRegionAnalysisRepository._get_since_time(days)

        query = (
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
            )
            .outerjoin(Detection, Detection.report_id == Report.id)
            .filter(Report.deleted_at.is_(None))
            .filter(Report.status.in_(AdminRegionAnalysisRepository.TARGET_STATUSES))
            .filter(Report.risk_level.in_(AdminRegionAnalysisRepository.TARGET_RISK_LEVELS))
            .filter(Report.latitude.isnot(None))
            .filter(Report.longitude.isnot(None))
            .filter(Report.created_at >= since_time)
        )

        if detected_label and detected_label != "all":
            query = query.filter(Detection.detected_label == detected_label)

        if risk_level and risk_level != "all":
            query = query.filter(Report.risk_level == risk_level)

        return query.order_by(Report.created_at.desc()).all()

    @staticmethod
    def get_rock_points_by_days(days=30, risk_level=None):
        since_time = AdminRegionAnalysisRepository._get_since_time(days)

        query = (
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
            )
            .join(Detection, Detection.report_id == Report.id)
            .filter(Report.deleted_at.is_(None))
            .filter(Report.status.in_(AdminRegionAnalysisRepository.TARGET_STATUSES))
            .filter(Report.risk_level.in_(AdminRegionAnalysisRepository.TARGET_RISK_LEVELS))
            .filter(Report.latitude.isnot(None))
            .filter(Report.longitude.isnot(None))
            .filter(Report.created_at >= since_time)
            .filter(Detection.detected_label == "rock")
        )

        if risk_level and risk_level != "all":
            query = query.filter(Report.risk_level == risk_level)

        return query.order_by(Report.created_at.desc()).all()

    @staticmethod
    def get_summary_data(days=30, detected_label=None, risk_level=None):
        since_time = AdminRegionAnalysisRepository._get_since_time(days)

        total_query = (
            db.session.query(func.count(func.distinct(Report.id)))
            .outerjoin(Detection, Detection.report_id == Report.id)
            .filter(Report.deleted_at.is_(None))
            .filter(Report.status.in_(AdminRegionAnalysisRepository.TARGET_STATUSES))
            .filter(Report.risk_level.in_(AdminRegionAnalysisRepository.TARGET_RISK_LEVELS))
            .filter(Report.created_at >= since_time)
        )

        if detected_label and detected_label != "all":
            total_query = total_query.filter(Detection.detected_label == detected_label)

        if risk_level and risk_level != "all":
            total_query = total_query.filter(Report.risk_level == risk_level)

        total_incidents = total_query.scalar() or 0

        hotspot_query = (
            db.session.query(
                Report.location_text,
                func.count(Report.id).label("cnt")
            )
            .outerjoin(Detection, Detection.report_id == Report.id)
            .filter(Report.deleted_at.is_(None))
            .filter(Report.status.in_(AdminRegionAnalysisRepository.TARGET_STATUSES))
            .filter(Report.risk_level.in_(AdminRegionAnalysisRepository.TARGET_RISK_LEVELS))
            .filter(Report.created_at >= since_time)
            .filter(Report.location_text.isnot(None))
            .filter(Report.location_text != "")
        )

        if detected_label and detected_label != "all":
            hotspot_query = hotspot_query.filter(Detection.detected_label == detected_label)

        if risk_level and risk_level != "all":
            hotspot_query = hotspot_query.filter(Report.risk_level == risk_level)

        hotspot_rows = (
            hotspot_query
            .group_by(Report.location_text)
            .having(func.count(Report.id) >= 2)
            .all()
        )

        total_detection_query = (
            db.session.query(func.count(Detection.id))
            .join(Report, Detection.report_id == Report.id)
            .filter(Report.deleted_at.is_(None))
            .filter(Report.status.in_(AdminRegionAnalysisRepository.TARGET_STATUSES))
            .filter(Report.risk_level.in_(AdminRegionAnalysisRepository.TARGET_RISK_LEVELS))
            .filter(Report.created_at >= since_time)
        )

        if risk_level and risk_level != "all":
            total_detection_query = total_detection_query.filter(Report.risk_level == risk_level)

        total_detection_count = total_detection_query.scalar() or 0

        rock_detection_query = (
            db.session.query(func.count(Detection.id))
            .join(Report, Detection.report_id == Report.id)
            .filter(Report.deleted_at.is_(None))
            .filter(Report.status.in_(AdminRegionAnalysisRepository.TARGET_STATUSES))
            .filter(Report.risk_level.in_(AdminRegionAnalysisRepository.TARGET_RISK_LEVELS))
            .filter(Report.created_at >= since_time)
            .filter(Detection.detected_label == "rock")
        )

        if risk_level and risk_level != "all":
            rock_detection_query = rock_detection_query.filter(Report.risk_level == risk_level)

        if detected_label and detected_label != "all":
            if detected_label == "rock":
                rock_detection_count = rock_detection_query.scalar() or 0
            else:
                rock_detection_count = 0
        else:
            rock_detection_count = rock_detection_query.scalar() or 0

        rock_ratio = round((rock_detection_count / total_detection_count) * 100, 1) if total_detection_count > 0 else 0.0

        emergency_query = (
            db.session.query(func.count(Report.id))
            .outerjoin(Detection, Detection.report_id == Report.id)
            .filter(Report.deleted_at.is_(None))
            .filter(Report.status.in_(AdminRegionAnalysisRepository.TARGET_STATUSES))
            .filter(Report.risk_level == "긴급")
            .filter(Report.created_at >= since_time)
        )

        if detected_label and detected_label != "all":
            emergency_query = emergency_query.filter(Detection.detected_label == detected_label)

        if risk_level and risk_level != "all":
            emergency_query = emergency_query.filter(Report.risk_level == risk_level)

        emergency_count = emergency_query.scalar() or 0

        return {
            "total_incidents": total_incidents,
            "hotspot_regions": len(hotspot_rows),
            "rock_ratio": rock_ratio,
            "emergency_count": emergency_count
        }

    @staticmethod
    def get_label_distribution(days=30, risk_level=None):
        since_time = AdminRegionAnalysisRepository._get_since_time(days)

        query = (
            db.session.query(
                Detection.detected_label.label("label"),
                func.count(Detection.id).label("count")
            )
            .join(Report, Detection.report_id == Report.id)
            .filter(Report.deleted_at.is_(None))
            .filter(Report.status.in_(AdminRegionAnalysisRepository.TARGET_STATUSES))
            .filter(Report.risk_level.in_(AdminRegionAnalysisRepository.TARGET_RISK_LEVELS))
            .filter(Report.created_at >= since_time)
        )

        if risk_level and risk_level != "all":
            query = query.filter(Report.risk_level == risk_level)

        return (
            query
            .group_by(Detection.detected_label)
            .order_by(func.count(Detection.id).desc())
            .all()
        )

    @staticmethod
    def get_risk_distribution(days=30, detected_label=None):
        since_time = AdminRegionAnalysisRepository._get_since_time(days)

        query = (
            db.session.query(
                Report.risk_level.label("risk_level"),
                func.count(func.distinct(Report.id)).label("count")
            )
            .outerjoin(Detection, Detection.report_id == Report.id)
            .filter(Report.deleted_at.is_(None))
            .filter(Report.status.in_(AdminRegionAnalysisRepository.TARGET_STATUSES))
            .filter(Report.risk_level.in_(AdminRegionAnalysisRepository.TARGET_RISK_LEVELS))
            .filter(Report.created_at >= since_time)
        )

        if detected_label and detected_label != "all":
            query = query.filter(Detection.detected_label == detected_label)

        return query.group_by(Report.risk_level).all()

    @staticmethod
    def get_top_regions(days=30, detected_label=None, risk_level=None, limit=10):
        since_time = AdminRegionAnalysisRepository._get_since_time(days)

        risk_score = case(
            (Report.risk_level == "긴급", 3),
            (Report.risk_level == "위험", 2),
            (Report.risk_level == "주의", 1),
            else_=0
        )

        query = (
            db.session.query(
                Report.location_text.label("location_text"),
                func.count(func.distinct(Report.id)).label("incident_count"),
                func.max(risk_score).label("max_risk_score")
            )
            .outerjoin(Detection, Detection.report_id == Report.id)
            .filter(Report.deleted_at.is_(None))
            .filter(Report.status.in_(AdminRegionAnalysisRepository.TARGET_STATUSES))
            .filter(Report.risk_level.in_(AdminRegionAnalysisRepository.TARGET_RISK_LEVELS))
            .filter(Report.created_at >= since_time)
            .filter(Report.location_text.isnot(None))
            .filter(Report.location_text != "")
        )

        if detected_label and detected_label != "all":
            query = query.filter(Detection.detected_label == detected_label)

        if risk_level and risk_level != "all":
            query = query.filter(Report.risk_level == risk_level)

        return (
            query
            .group_by(Report.location_text)
            .order_by(func.count(func.distinct(Report.id)).desc(), func.max(risk_score).desc())
            .limit(limit)
            .all()
        )