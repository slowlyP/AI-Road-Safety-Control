from datetime import datetime
from sqlalchemy import case

from app.extensions import db
from app.models.alert_model import Alert
from app.models.report_model import Report
from app.models.detection_model import Detection
from app.models.report_file_model import ReportFile


class RealtimeAlertRepository:
    """
    실시간 위험 알림 전용 Repository

    역할
    - 확인 대기 / 확인 완료 알림 목록 조회
    - 확인 대기 개수 조회
    - 단건 조회
    - 확인 완료 처리
    - 전체 확인 완료 처리
    - 새 알림 저장
    """

    TARGET_ALERT_LEVELS = ["위험", "긴급"]

    @staticmethod
    def _base_alert_query():
        """
        공통 알림 목록 조회 쿼리
        """
        return (
            db.session.query(
                Alert.id.label("alert_id"),
                Alert.report_id.label("report_id"),
                Alert.detection_id.label("detection_id"),
                Alert.alert_level.label("alert_level"),
                Alert.message.label("message"),
                Alert.is_read.label("is_read"),
                Alert.created_at.label("created_at"),

                Report.title.label("report_title"),
                Report.location_text.label("location_text"),
                Report.risk_level.label("risk_level"),

                Detection.detected_label.label("detected_label"),
                Detection.confidence.label("confidence"),

                ReportFile.file_type.label("file_type"),
                ReportFile.file_path.label("file_path"),
                ReportFile.original_name.label("original_name")
            )
            .join(Report, Alert.report_id == Report.id)
            .outerjoin(Detection, Alert.detection_id == Detection.id)
            .outerjoin(ReportFile, Detection.file_id == ReportFile.id)
            .filter(Alert.alert_level.in_(RealtimeAlertRepository.TARGET_ALERT_LEVELS))
        )

    @staticmethod
    def _risk_order():
        """
        정렬 기준:
        긴급 > 위험
        """
        return case(
            (Alert.alert_level == "긴급", 2),
            (Alert.alert_level == "위험", 1),
            else_=0
        )

    @staticmethod
    def find_pending_realtime_alerts(limit=50):
        """
        확인 대기 알림 목록 조회
        """
        rows = (
            RealtimeAlertRepository._base_alert_query()
            .filter(Alert.is_read.is_(False))
            .order_by(
                RealtimeAlertRepository._risk_order().desc(),
                Alert.created_at.desc()
            )
            .limit(limit)
            .all()
        )
        return rows

    @staticmethod
    def find_checked_realtime_alerts(limit=50):
        """
        확인 완료 알림 목록 조회
        """
        rows = (
            RealtimeAlertRepository._base_alert_query()
            .filter(Alert.is_read.is_(True))
            .order_by(
                RealtimeAlertRepository._risk_order().desc(),
                Alert.created_at.desc()
            )
            .limit(limit)
            .all()
        )
        return rows

    @staticmethod
    def count_pending_alerts():
        """
        확인 대기 위험/긴급 알림 개수 조회
        """
        return (
            db.session.query(Alert)
            .filter(
                Alert.alert_level.in_(RealtimeAlertRepository.TARGET_ALERT_LEVELS),
                Alert.is_read.is_(False)
            )
            .count()
        )

    @staticmethod
    def find_alert_by_id(alert_id):
        """
        알림 단건 조회
        """
        return (
            Alert.query
            .filter(Alert.id == alert_id)
            .first()
        )

    @staticmethod
    def mark_as_checked(alert):
        """
        특정 알림 확인 완료 처리
        """
        if not alert:
            return None

        alert.is_read = True
        alert.read_at = datetime.now()
        db.session.commit()

        return alert

    @staticmethod
    def mark_all_as_checked():
        """
        전체 위험/긴급 알림 확인 완료 처리
        """
        alerts = (
            Alert.query
            .filter(
                Alert.alert_level.in_(RealtimeAlertRepository.TARGET_ALERT_LEVELS),
                Alert.is_read.is_(False)
            )
            .all()
        )

        if not alerts:
            return 0

        now = datetime.now()

        for alert in alerts:
            alert.is_read = True
            alert.read_at = now

        db.session.commit()
        return len(alerts)

    @staticmethod
    def create_alert(report_id, detection_id, alert_level, message):
        """
        새 실시간 알림 생성
        """
        new_alert = Alert(
            report_id=report_id,
            detection_id=detection_id,
            alert_level=alert_level,
            message=message,
            is_read=False
        )

        db.session.add(new_alert)
        db.session.flush()  # new_alert.id 확보

        return new_alert