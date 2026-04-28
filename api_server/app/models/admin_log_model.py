from app.extensions import db


class AdminLog(db.Model):
    """
    관리자 작업 로그
    """

    __tablename__ = "admin_logs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    admin_user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id"),
        nullable=False
    )

    action_type = db.Column(db.String(100), nullable=False)

    target_type = db.Column(db.String(100), nullable=False)

    target_id = db.Column(db.BigInteger)

    action_detail = db.Column(db.String(255))

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )