"""
관리자 대시보드 서비스
"""

from sqlalchemy import func

from app.extensions import db
from app.models.user_model import User
from app.models.report_model import Report
from app.models.role_request_model import RoleRequest


class AdminService:
    @staticmethod
    def get_dashboard_stats():
        # 총 회원 수
        total_users = (
            db.session.query(func.count(User.id))
            .filter(User.deleted_at.is_(None))
            .scalar()
        )

        # 총 신고 수
        total_reports = (
            db.session.query(func.count(Report.id))
            .filter(Report.deleted_at.is_(None))
            .scalar()
        )

        # 위험도 통계
        risk_stats = (
            db.session.query(
                Report.risk_level,
                func.count(Report.id)
            )
            .filter(Report.deleted_at.is_(None))
            .group_by(Report.risk_level)
            .all()
        )

        risk_result = {
            "낮음": 0,
            "주의": 0,
            "위험": 0,
            "긴급": 0
        }
        for level, count in risk_stats:
            risk_result[level] = count

        # 상태 통계
        status_stats = (
            db.session.query(
                Report.status,
                func.count(Report.id)
            )
            .filter(Report.deleted_at.is_(None))
            .group_by(Report.status)
            .all()
        )

        status_result = {
            "접수": 0,
            "확인중": 0,
            "처리완료": 0,
            "오탐": 0
        }
        for status, count in status_stats:
            status_result[status] = count

        # 최근 신고
        recent_reports = (
            Report.query
            .filter(Report.deleted_at.is_(None))
            .order_by(Report.created_at.desc())
            .limit(5)
            .all()
        )

        recent_result = [
            {
                "id": r.id,
                "title": r.title,
                "risk_level": r.risk_level,
                "status": r.status,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else ""
            }
            for r in recent_reports
        ]

        # 대기 중 권한 신청
        pending_requests = (
            RoleRequest.query
            .join(User, RoleRequest.user_id == User.id)
            .filter(
                RoleRequest.status == "대기",
                User.deleted_at.is_(None)
            )
            .order_by(RoleRequest.created_at.desc())
            .limit(5)
            .all()
        )

        pending_request_result = [
            {
                "id": req.id,
                "user_id": req.user.id if req.user else None,
                "username": req.user.username if req.user else "-",
                "name": req.user.name if req.user else "-",
                "request_reason": req.request_reason,
                "created_at": req.created_at.strftime("%Y-%m-%d %H:%M") if req.created_at else ""
            }
            for req in pending_requests
        ]

        return {
            "total_users": total_users,
            "total_reports": total_reports,
            "risk_stats": risk_result,
            "status_stats": status_result,
            "recent_reports": recent_result,
            "pending_role_requests": pending_request_result,
            "pending_role_request_count": len(pending_request_result)
        }