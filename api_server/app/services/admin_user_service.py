"""
관리자 회원 관리 서비스

역할
- 회원 목록 조회
- 회원 상세 조회
- 회원 권한 변경
- 회원 삭제
- 권한 신청 목록 조회
- 권한 신청 승인 / 거절
- 권한 신청 이력 조회
- 회원 신고 이력 조회
"""

from datetime import datetime

from app.extensions import db
from app.models.user_model import User
from app.models.role_request_model import RoleRequest
from app.models.report_model import Report


class AdminUserService:
    def get_user_list(self, page=1, per_page=10, keyword=None, role=None):
        query = User.query.filter(User.deleted_at.is_(None))

        if keyword:
            search = f"%{keyword}%"
            query = query.filter(
                (User.username.like(search)) |
                (User.name.like(search))
            )

        if role:
            query = query.filter(User.role == role)

        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        users = [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "name": u.name,
                "role": u.role,
                "created_at": u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else ""
            }
            for u in pagination.items
        ]

        return {
            "users": users,
            "pagination": pagination
        }

    def get_user_detail(self, user_id):
        user = User.query.filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()

        if not user:
            raise ValueError("존재하지 않는 회원입니다.")

        role_requests = (
            RoleRequest.query
            .filter(RoleRequest.user_id == user_id)
            .order_by(RoleRequest.created_at.desc())
            .all()
        )

        reports = (
            Report.query
            .filter(
                Report.user_id == user_id,
                Report.deleted_at.is_(None)
            )
            .order_by(Report.created_at.desc())
            .all()
        )

        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else ""
            },
            "role_requests": [
                {
                    "id": r.id,
                    "request_reason": r.request_reason,
                    "status": r.status,
                    "reviewed_by": r.reviewed_by,
                    "reviewed_by_name": r.reviewer.name if r.reviewer and r.reviewer.name else (
                        r.reviewer.username if r.reviewer else "-"
                    ),
                    "reviewed_at": r.reviewed_at.strftime("%Y-%m-%d %H:%M") if r.reviewed_at else "-",
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else ""
                }
                for r in role_requests
            ],
            "reports": [
                {
                    "id": report.id,
                    "title": report.title,
                    "risk_level": report.risk_level,
                    "status": report.status,
                    "created_at": report.created_at.strftime("%Y-%m-%d %H:%M") if report.created_at else ""
                }
                for report in reports
            ]
        }

    def update_user_role(self, user_id, role, admin_id):
        if role not in ["user", "admin"]:
            raise ValueError("올바르지 않은 권한 값입니다.")

        user = User.query.filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()

        if not user:
            raise ValueError("존재하지 않는 회원입니다.")

        if user.id == admin_id and role != "admin":
            raise ValueError("본인 계정의 관리자 권한은 해제할 수 없습니다.")

        if user.role == "admin" and role != "admin":
            admin_count = (
                User.query
                .filter(
                    User.role == "admin",
                    User.deleted_at.is_(None)
                )
                .count()
            )

            if admin_count <= 1:
                raise ValueError("마지막 관리자는 일반 회원으로 변경할 수 없습니다.")

        user.role = role
        db.session.commit()

        return user

    def delete_user(self, user_id, admin_id):
        user = User.query.filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()

        if not user:
            raise ValueError("존재하지 않는 회원입니다.")

        if user.id == admin_id:
            raise ValueError("본인 계정은 삭제할 수 없습니다.")

        if user.role == "admin":
            admin_count = (
                User.query
                .filter(
                    User.role == "admin",
                    User.deleted_at.is_(None)
                )
                .count()
            )

            if admin_count <= 1:
                raise ValueError("마지막 관리자는 삭제할 수 없습니다.")

        user.deleted_at = db.func.now()
        db.session.commit()

        return user

    def get_role_request_list(self, page=1, per_page=10, status=None, keyword=None):
        query = (
            RoleRequest.query
            .join(User, RoleRequest.user_id == User.id)
            .filter(User.deleted_at.is_(None))
        )

        if status:
            query = query.filter(RoleRequest.status == status)

        if keyword:
            search = f"%{keyword}%"
            query = query.filter(
                (User.username.like(search)) |
                (User.name.like(search))
            )

        pagination = query.order_by(RoleRequest.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        requests = [
            {
                "id": req.id,
                "user_id": req.user.id if req.user else None,
                "username": req.user.username if req.user else "-",
                "name": req.user.name if req.user else "-",
                "request_reason": req.request_reason,
                "status": req.status,
                "reviewed_by": req.reviewed_by,
                "reviewed_by_name": req.reviewer.name if req.reviewer and req.reviewer.name else (
                    req.reviewer.username if req.reviewer else "-"
                ),
                "reviewed_at": req.reviewed_at.strftime("%Y-%m-%d %H:%M") if req.reviewed_at else "-",
                "created_at": req.created_at.strftime("%Y-%m-%d %H:%M") if req.created_at else ""
            }
            for req in pagination.items
        ]

        return {
            "requests": requests,
            "pagination": pagination
        }

    def review_role_request(self, request_id, admin_id, status):
        if status not in ["승인", "거절"]:
            raise ValueError("처리 상태는 승인 또는 거절만 가능합니다.")

        role_request = RoleRequest.query.filter(
            RoleRequest.id == request_id
        ).first()

        if not role_request:
            raise ValueError("권한 신청 내역을 찾을 수 없습니다.")

        if role_request.status != "대기":
            raise ValueError("이미 처리된 권한 신청입니다.")

        user = User.query.filter(
            User.id == role_request.user_id,
            User.deleted_at.is_(None)
        ).first()

        if not user:
            raise ValueError("신청한 회원 정보를 찾을 수 없습니다.")

        role_request.status = status
        role_request.reviewed_by = admin_id
        role_request.reviewed_at = datetime.now()

        if status == "승인":
            user.role = "admin"

        db.session.commit()

        return role_request