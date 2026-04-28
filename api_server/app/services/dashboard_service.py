"""
관리자 대시보드 서비스

역할
- 관리자 대시보드에 필요한 데이터를 조합해서 반환한다.
- repository 또는 model 조회 결과를 라우터가 쓰기 좋은 형태로 가공한다.
"""

from app.models.report_model import Report
from app.models.role_request_model import RoleRequest
from app.models.user_model import User
from app.extensions import db


class DashboardService:
    """
    관리자 대시보드 서비스 클래스
    """

    def get_dashboard_data(self) -> dict:
        """
        대시보드 전체 데이터를 조회하여 딕셔너리 형태로 반환한다.
        """
        total_reports = self.get_total_reports_count()
        completed_reports = self.get_completed_reports_count()
        pending_reports = self.get_pending_reports_count()
        false_reports = self.get_false_reports_count()
        recent_reports = self.get_recent_reports(limit=5)
        pending_role_requests = self.get_pending_role_requests(limit=5)

        return {
            "total_reports": total_reports,
            "completed_reports": completed_reports,
            "pending_reports": pending_reports,
            "false_reports": false_reports,
            "recent_reports": recent_reports,
            "pending_role_requests": pending_role_requests,
        }

    def get_total_reports_count(self) -> int:
        """
        삭제되지 않은 전체 신고 수 조회
        """
        return Report.query.filter(Report.deleted_at.is_(None)).count()

    def get_completed_reports_count(self) -> int:
        """
        처리 완료 상태 신고 수 조회
        """
        return Report.query.filter(
            Report.status == "처리완료",
            Report.deleted_at.is_(None)
        ).count()

    def get_pending_reports_count(self) -> int:
        """
        미처리 신고 수 조회
        기준:
        - 접수
        - 확인중
        """
        return Report.query.filter(
            Report.status.in_(["접수", "확인중"]),
            Report.deleted_at.is_(None)
        ).count()

    def get_false_reports_count(self) -> int:
        """
        오탐 신고 수 조회
        """
        return Report.query.filter(
            Report.status == "오탐",
            Report.deleted_at.is_(None)
        ).count()

    def get_recent_reports(self, limit: int = 5) -> list[dict]:
        """
        최근 신고 목록 조회

        반환 형식:
        [
            {
                "id": 1,
                "title": "...",
                "risk_level": "...",
                "status": "...",
                "created_at": "2026-03-13 10:20"
            }
        ]
        """
        reports = (
            Report.query
            .filter(Report.deleted_at.is_(None))
            .order_by(Report.created_at.desc())
            .limit(limit)
            .all()
        )

        result = []
        for report in reports:
            result.append({
                "id": report.id,
                "title": report.title,
                "risk_level": report.risk_level,
                "status": report.status,
                "created_at": report.created_at.strftime("%Y-%m-%d %H:%M") if report.created_at else "",
            })

        return result

    def get_pending_role_requests(self, limit: int = 5) -> list[dict]:
        """
        대기 중인 관리자 권한 신청 목록 조회

        User 테이블과 조인하여 신청자 이름도 함께 가져온다.
        """
        rows = (
            db.session.query(RoleRequest, User)
            .join(User, RoleRequest.user_id == User.id)
            .filter(RoleRequest.status == "대기")
            .order_by(RoleRequest.created_at.desc())
            .limit(limit)
            .all()
        )

        result = []
        for role_request, user in rows:
            result.append({
                "id": role_request.id,
                "user_id": user.id,
                "user_name": user.name,
                "request_reason": role_request.request_reason,
                "status": role_request.status,
                "created_at": role_request.created_at.strftime("%Y-%m-%d %H:%M") if role_request.created_at else "",
            })

        return result