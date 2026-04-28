"""
관리자 권한 신청 Repository

role_requests 테이블 접근을 담당한다.
"""

from app.extensions import db
from app.models.role_request_model import RoleRequest


class RoleRequestRepository:

    @staticmethod
    def create_request(user_id: int, reason: str):
        """
        관리자 권한 신청 생성
        """

        role_request = RoleRequest(
            user_id=user_id,
            request_reason=reason
        )

        db.session.add(role_request)
        db.session.commit()

        return role_request


    @staticmethod
    def get_requests():
        """
        전체 권한 신청 목록 조회 (관리자용)
        """

        return RoleRequest.query.order_by(
            RoleRequest.created_at.desc()
        ).all()


    @staticmethod
    def get_user_request(user_id: int):
        """
        특정 사용자의 권한 신청 조회
        """

        return RoleRequest.query.filter_by(
            user_id=user_id
        ).first()


    @staticmethod
    def update_status(request_id: int, status: str, admin_id: int):
        """
        권한 신청 상태 업데이트
        """

        request = RoleRequest.query.get(request_id)

        if not request:
            return None

        request.status = status
        request.reviewed_by = admin_id

        db.session.commit()

        return request