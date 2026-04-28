from app.extensions import db


class RoleRequest(db.Model):
    """
    관리자 권한 신청 테이블
    """

    __tablename__ = "role_requests"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    # 신청 사용자
    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # 신청 사유
    request_reason = db.Column(db.Text)

    # 상태
    status = db.Column(
        db.Enum("대기", "승인", "거절"),
        default="대기",
        nullable=False
    )

    # 검토 관리자
    reviewed_by = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id")
    )

    # 검토 시간
    reviewed_at = db.Column(db.DateTime)

    # 생성 시간
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    # 🔹 신청자 관계
    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref="role_requests"
    )

    # 🔹 검토 관리자 관계
    reviewer = db.relationship(
        "User",
        foreign_keys=[reviewed_by]
    )