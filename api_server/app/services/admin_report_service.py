"""
관리자 신고 관리 서비스

역할
- 관리자 신고 목록 조회
- 관리자 신고 상세 조회
- 관리자 신고 상태 변경
"""

from datetime import datetime
from sqlalchemy import case

from app.extensions import db
from app.models.report_model import Report
from app.models.report_status_log_model import ReportStatusLog
from app.models.report_file_model import ReportFile
from app.models.detection_model import Detection
from app.models.user_model import User


class AdminReportService:
    def get_report_list(
        self,
        page=1,
        per_page=10,
        status=None,
        risk_level=None,
        keyword=None,
        sort=None
    ):
        query = Report.query.filter(Report.deleted_at.is_(None))

        if status:
            query = query.filter(Report.status == status)

        if risk_level:
            query = query.filter(Report.risk_level == risk_level)

        if keyword:
            search = f"%{keyword}%"
            query = query.filter(Report.title.like(search))

        # 최신순 버튼 눌렀을 때
        if sort == "latest":
            query = query.order_by(Report.created_at.desc())

        # 기본 정렬
        else:
            status_priority = case(
                (Report.status == "접수", 0),
                else_=1
            )

            risk_priority = case(
                (Report.risk_level == "긴급", 0),
                (Report.risk_level == "위험", 1),
                (Report.risk_level == "주의", 2),
                (Report.risk_level == "낮음", 3),
                else_=4
            )

            query = query.order_by(
                status_priority.asc(),   # 접수 먼저
                risk_priority.asc(),     # 접수 안에서는 위험도 높은 순
                Report.created_at.desc() # 같은 조건이면 최신순
            )

        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        reports = [
            {
                "id": r.id,
                "title": r.title,
                "risk_level": r.risk_level,
                "status": r.status,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else ""
            }
            for r in pagination.items
        ]

        return {
            "reports": reports,
            "pagination": pagination
        }

    def get_report_detail(self, report_id):
        """
        관리자 신고 상세 조회
        - 신고 기본 정보
        - 첨부 파일 목록
        - 상태 변경 이력
        - AI 분석 결과
        """

        report = Report.query.filter(
            Report.id == report_id,
            Report.deleted_at.is_(None)
        ).first()

        if not report:
            raise ValueError("존재하지 않는 신고입니다.")

        files = (
            ReportFile.query
            .filter(
                ReportFile.report_id == report_id,
                ReportFile.deleted_at.is_(None),
                ReportFile.is_active.is_(True)
            )
            .order_by(ReportFile.id.asc())
            .all()
        )

        status_logs = (
            ReportStatusLog.query
            .filter(ReportStatusLog.report_id == report_id)
            .order_by(ReportStatusLog.created_at.desc(), ReportStatusLog.id.desc())
            .all()
        )

        detections = (
            Detection.query
            .filter(Detection.report_id == report_id)
            .order_by(Detection.time_sec.asc(), Detection.id.asc())
            .all()
        )

        report_data = {
            "id": report.id,
            "title": report.title,
            "content": report.content,
            "risk_level": report.risk_level,
            "status": report.status,
            "report_type": report.report_type,
            "location_text": report.location_text,
            "created_at": report.created_at.strftime("%Y-%m-%d %H:%M") if report.created_at else ""
        }

        file_list = []
        for f in files:
            raw_path = (getattr(f, "file_path", "") or "").replace("\\", "/").lstrip("/")

            # static/uploads/... 형태면 static 기준 경로만 넘김
            if raw_path.startswith("app/static/"):
                preview_path = raw_path[len("app/static/"):]
            elif raw_path.startswith("static/"):
                preview_path = raw_path[len("static/"):]
            else:
                preview_path = raw_path

            file_list.append({
                "id": f.id,
                "original_name": getattr(f, "original_name", ""),
                "stored_name": getattr(f, "stored_name", ""),
                "file_path": raw_path,
                "preview_path": preview_path,
                "file_type": getattr(f, "file_type", ""),
                "file_size": getattr(f, "file_size", 0)
            })

        status_log_list = []
        for log in status_logs:
            manager_name = "-"

            if log.changed_by:
                admin_user = User.query.filter(User.id == log.changed_by).first()
                if admin_user:
                    manager_name = admin_user.name or admin_user.username or f"관리자#{log.changed_by}"

            status_log_list.append({
                "id": log.id,
                "old_status": log.old_status,
                "new_status": log.new_status,
                "changed_by": log.changed_by,
                "changed_by_name": manager_name,
                "memo": log.memo,
                "created_at": log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else ""
            })

        ai_analysis = [
            {
                "id": d.id,
                "file_id": d.file_id,
                "detected_label": d.detected_label,
                "label_kor": d.label_kor,
                "confidence": float(d.confidence) if d.confidence is not None else 0,
                "bbox": [d.bbox_x1, d.bbox_y1, d.bbox_x2, d.bbox_y2],
                "frame_no": d.frame_no,
                "time_sec": float(d.time_sec) if d.time_sec is not None else None,
                "frame_width": d.frame_width,
                "frame_height": d.frame_height,

                "detected_at": d.detected_at.strftime("%Y-%m-%d %H:%M") if d.detected_at else ""
            }

            for d in detections
        ]

        return {
            "report": report_data,
            "files": file_list,
            "status_logs": status_log_list,
            "ai_analysis": ai_analysis
        }

    def update_report_status(self, report_id, status, changed_by=None, memo=None):
        """
        관리자 신고 상태 변경
        """

        report = Report.query.filter(
            Report.id == report_id,
            Report.deleted_at.is_(None)
        ).first()

        if not report:
            raise ValueError("존재하지 않는 신고입니다.")

        old_status = report.status

        # 같은 상태면 로그 저장하지 않음
        if old_status == status:
            return None

        report.status = status

        status_log = ReportStatusLog(
            report_id=report.id,
            old_status=old_status,
            new_status=status,
            changed_by=changed_by,
            memo=memo if memo else None,
            created_at=datetime.now()
        )

        db.session.add(status_log)
        db.session.commit()

        return True