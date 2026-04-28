from app.models.role_request_model import RoleRequest
from app.models.user_model import User
from app.extensions import db
from app.common.exceptions import BaseCustomException


class AdminRoleRequestService:

    @staticmethod
    def get_role_request_list():
        return (
            RoleRequest.query
            .join(User, RoleRequest.user_id == User.id)
            .order_by(RoleRequest.created_at.desc())
            .all()
        )

    @staticmethod
    def get_role_request_detail(request_id):
        role_request = (
            RoleRequest.query
            .join(User, RoleRequest.user_id == User.id)
            .filter(RoleRequest.id == request_id)
            .first()
        )

        if not role_request:
            raise BaseCustomException("권한 신청 내역을 찾을 수 없습니다.", 404)

        return role_request

    @staticmethod
    def review_role_request(request_id, admin_user_id, status, review_comment=""):
        if status not in ["승인", "거절"]:
            raise BaseCustomException("처리 상태가 올바르지 않습니다.", 400)

        role_request = RoleRequest.query.filter_by(id=request_id).first()

        if not role_request:
            raise BaseCustomException("권한 신청 내역을 찾을 수 없습니다.", 404)

        if role_request.status != "대기":
            raise BaseCustomException("이미 처리된 신청입니다.", 400)

        role_request.status = status
        role_request.reviewed_by = admin_user_id
        role_request.review_comment = review_comment

        if status == "승인":
            user = User.query.filter_by(id=role_request.user_id).first()
            if user:
                user.role = "admin"

        db.session.commit()
        return role_request