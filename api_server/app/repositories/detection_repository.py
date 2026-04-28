from datetime import datetime, timedelta
from sqlalchemy import func, case
from app.extensions import db
from app.models import Detection, Report, ReportFile


class DetectionRepository:
    """
    AI 탐지 결과 전용 Repository

    역할
    - AI 탐지 목록 조회
    - AI 탐지 상세 조회
    - AI 통계 데이터 집계
    """

    # -----------------------------
    # 내부 공통 메서드
    # -----------------------------
    @staticmethod
    def _apply_period_filter(query, date_column, period="30d"):
        """
        기간 필터 적용
        period:
        - 7d
        - 30d
        - all
        """
        if period == "7d":
            start_date = datetime.now() - timedelta(days=7)
            query = query.filter(date_column >= start_date)
        elif period == "30d":
            start_date = datetime.now() - timedelta(days=30)
            query = query.filter(date_column >= start_date)

        return query

    @staticmethod
    def _apply_file_type_filter(query, file_type="all"):
        """
        파일 유형 필터 적용
        file_type:
        - all
        - image
        - video
        """
        if file_type == "image":
            query = query.filter(ReportFile.file_type == "이미지")
        elif file_type == "video":
            query = query.filter(ReportFile.file_type == "영상")

        return query

    # -----------------------------
    # 목록 / 상세
    # -----------------------------
    @staticmethod
    def find_detection_list(page=1, per_page=10, label=None, min_conf=None, max_conf=None, status=None):
        """
        AI 탐지 로그 목록 조회

        필터
        - label        : 탐지 라벨명
        - min_conf     : 최소 confidence
        - max_conf     : 최대 confidence
        - status       : 연결된 신고 상태
        """

        query = (
            db.session.query(
                Detection.id.label("detection_id"),
                Detection.detected_label,
                Detection.confidence,
                Detection.detected_at,
                Report.id.label("report_id"),
                Report.title.label("report_title"),
                Report.risk_level,
                Report.status,
                ReportFile.file_type,
                ReportFile.file_path
            )
            .join(Report, Detection.report_id == Report.id)
            .outerjoin(ReportFile, Detection.file_id == ReportFile.id)
        )

        if label:
            query = query.filter(Detection.detected_label == label)

        if min_conf is not None:
            query = query.filter(Detection.confidence >= min_conf)

        if max_conf is not None:
            query = query.filter(Detection.confidence <= max_conf)

        if status:
            query = query.filter(Report.status == status)

        query = query.order_by(Detection.detected_at.desc())

        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def find_detection_detail(detection_id):
        """
        AI 탐지 상세 조회
        """
        return (
            db.session.query(
                Detection,
                Report,
                ReportFile
            )
            .join(Report, Detection.report_id == Report.id)
            .outerjoin(ReportFile, Detection.file_id == ReportFile.id)
            .filter(Detection.id == detection_id)
            .first()
        )

    # -----------------------------
    # KPI 카드
    # -----------------------------
    @staticmethod
    def count_all_detections(period="30d", file_type="all"):
        """
        전체 탐지 건수
        """
        query = (
            db.session.query(func.count(Detection.id))
            .join(Report, Detection.report_id == Report.id)
            .outerjoin(ReportFile, Detection.file_id == ReportFile.id)
        )

        query = DetectionRepository._apply_period_filter(query, Detection.detected_at, period)
        query = DetectionRepository._apply_file_type_filter(query, file_type)

        return query.scalar() or 0

    @staticmethod
    def get_average_confidence(period="30d", file_type="all"):
        """
        평균 confidence
        """
        query = (
            db.session.query(func.avg(Detection.confidence))
            .join(Report, Detection.report_id == Report.id)
            .outerjoin(ReportFile, Detection.file_id == ReportFile.id)
        )

        query = DetectionRepository._apply_period_filter(query, Detection.detected_at, period)
        query = DetectionRepository._apply_file_type_filter(query, file_type)

        return query.scalar() or 0.0

    @staticmethod
    def count_false_positives(period="30d", file_type="all"):
        """
        오탐 건수
        기준:
        - detection 존재
        - 연결된 report.status == '오탐'
        """
        query = (
            db.session.query(func.count(Detection.id))
            .join(Report, Detection.report_id == Report.id)
            .outerjoin(ReportFile, Detection.file_id == ReportFile.id)
            .filter(Report.status == "오탐")
        )

        query = DetectionRepository._apply_period_filter(query, Detection.detected_at, period)
        query = DetectionRepository._apply_file_type_filter(query, file_type)

        return query.scalar() or 0

    @staticmethod
    def count_final_judged_reports(period="30d", file_type="all"):
        """
        최종 판단 완료 건수
        기준:
        - 처리완료
        - 오탐
        """
        query = (
            db.session.query(func.count(func.distinct(Report.id)))
            .join(Detection, Detection.report_id == Report.id)
            .outerjoin(ReportFile, Detection.file_id == ReportFile.id)
            .filter(Report.status.in_(["처리완료", "오탐"]))
        )

        query = DetectionRepository._apply_period_filter(query, Detection.detected_at, period)
        query = DetectionRepository._apply_file_type_filter(query, file_type)

        return query.scalar() or 0

    # -----------------------------
    # 클래스별 통계
    # -----------------------------
    @staticmethod
    def get_label_statistics_by_file_type(file_type, period="30d"):
        """
        파일 유형별 클래스 통계
        file_type:
        - image
        - video
        """
        query = (
            db.session.query(
                Detection.detected_label,
                func.count(Detection.id).label("count")
            )
            .join(Report, Detection.report_id == Report.id)
            .outerjoin(ReportFile, Detection.file_id == ReportFile.id)
            .filter(Detection.detected_label.in_(["bag", "box", "rock", "tire"]))
            .filter(Report.status.in_(["처리완료", "오탐"]))
        )

        query = DetectionRepository._apply_period_filter(query, Detection.detected_at, period)
        query = DetectionRepository._apply_file_type_filter(query, file_type)

        return (
            query.group_by(Detection.detected_label)
            .order_by(func.count(Detection.id).desc())
            .all()
        )

    @staticmethod
    def get_monthly_label_statistics(period="30d"):
        """
        월별 클래스 통계
        """
        query = (
            db.session.query(
                func.date_format(Detection.detected_at, "%Y-%m").label("month"),
                Detection.detected_label,
                func.count(Detection.id).label("count")
            )
            .join(Report, Detection.report_id == Report.id)
            .outerjoin(ReportFile, Detection.file_id == ReportFile.id)
            .filter(Detection.detected_label.in_(["bag", "box", "rock", "tire"]))
            .filter(Report.status.in_(["처리완료", "오탐"]))
        )

        query = DetectionRepository._apply_period_filter(query, Detection.detected_at, period)

        return (
            query.group_by(
                func.date_format(Detection.detected_at, "%Y-%m"),
                Detection.detected_label
            )
            .order_by(func.date_format(Detection.detected_at, "%Y-%m").asc())
            .all()
        )

    @staticmethod
    def get_monthly_result_statistics(period="30d"):
        """
        월별 처리완료 / 오탐 추이
        """
        query = (
            db.session.query(
                func.date_format(Detection.detected_at, "%Y-%m").label("month"),
                func.count(
                    case((Report.status == "처리완료", 1))
                ).label("done_count"),
                func.count(
                    case((Report.status == "오탐", 1))
                ).label("false_positive_count")
            )
            .join(Report, Detection.report_id == Report.id)
            .outerjoin(ReportFile, Detection.file_id == ReportFile.id)
            .filter(Report.status.in_(["처리완료", "오탐"]))
        )

        query = DetectionRepository._apply_period_filter(query, Detection.detected_at, period)

        return (
            query.group_by(func.date_format(Detection.detected_at, "%Y-%m"))
            .order_by(func.date_format(Detection.detected_at, "%Y-%m").asc())
            .all()
        )

    # -----------------------------
    # confidence 분포
    # -----------------------------
    @staticmethod
    def get_confidence_distribution(period="30d", file_type="all"):
        """
        confidence 구간별 분포

        현재 기준:
        - 0~49
        - 50~69
        - 70~84
        - 85~100

        주의:
        confidence 값이 0~1 저장이면 구간식 수정 필요
        """
        query = (
            db.session.query(
                case(
                    (Detection.confidence < 50, "0~49"),
                    (Detection.confidence < 70, "50~69"),
                    (Detection.confidence < 85, "70~84"),
                    else_="85~100"
                ).label("range"),
                func.count(Detection.id).label("count")
            )
            .join(Report, Detection.report_id == Report.id)
            .outerjoin(ReportFile, Detection.file_id == ReportFile.id)
        )

        query = DetectionRepository._apply_period_filter(query, Detection.detected_at, period)
        query = DetectionRepository._apply_file_type_filter(query, file_type)

        return (
            query.group_by("range")
            .order_by("range")
            .all()
        )

    # -----------------------------
    # 기존 보조 통계
    # -----------------------------
    @staticmethod
    def get_label_statistics():
        """
        라벨별 탐지 건수
        """
        rows = (
            db.session.query(
                Detection.detected_label,
                func.count(Detection.id).label("count")
            )
            .group_by(Detection.detected_label)
            .order_by(func.count(Detection.id).desc())
            .all()
        )

        return rows

    @staticmethod
    def get_daily_detection_statistics(limit=7):
        """
        최근 N일 탐지 추이
        MySQL 기준: DATE(detected_at)
        """
        rows = (
            db.session.query(
                func.date(Detection.detected_at).label("date"),
                func.count(Detection.id).label("count")
            )
            .group_by(func.date(Detection.detected_at))
            .order_by(func.date(Detection.detected_at).desc())
            .limit(limit)
            .all()
        )

        return list(reversed(rows))

    @staticmethod
    def find_recent_false_positive_cases(limit=5):
        """
        최근 오탐 사례 조회
        """
        rows = (
            db.session.query(
                Detection.id.label("detection_id"),
                Detection.detected_label,
                Detection.confidence,
                Detection.detected_at,
                Report.id.label("report_id"),
                Report.title.label("report_title"),
                Report.status,
                ReportFile.file_type,
                ReportFile.file_path
            )
            .join(Report, Detection.report_id == Report.id)
            .outerjoin(ReportFile, Detection.file_id == ReportFile.id)
            .filter(Report.status == "오탐")
            .order_by(Detection.detected_at.desc())
            .limit(limit)
            .all()
        )

        return rows

    # -----------------------------
    # 모델 성능 지표
    # -----------------------------
    @staticmethod
    def get_latest_model_metrics():
        """
        최신 모델 성능 지표 조회

        현재 model_metrics 테이블이 아직 없으면
        일단 None 반환하도록 두고,
        추후 테이블 추가 후 구현
        """
        return None