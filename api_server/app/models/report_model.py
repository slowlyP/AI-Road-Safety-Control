from app.extensions import db


class Report(db.Model):
    """
    낙하물 신고 정보
    """

    __tablename__ = "reports"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id"),
        nullable=False
    )

    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)

    report_type = db.Column(
        db.Enum("이미지", "영상", "카메라")
    )

    location_text = db.Column(db.String(255))
    latitude = db.Column(db.Numeric(10, 7))
    longitude = db.Column(db.Numeric(10, 7))

    risk_level = db.Column(
        db.Enum("낮음", "주의", "위험", "긴급"),
        default="주의"
    )

    status = db.Column(
        db.Enum("접수", "확인중", "처리완료", "오탐"),
        default="접수"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    updated_at = db.Column(db.DateTime)
    deleted_at = db.Column(db.DateTime)

    files = db.relationship(
        "ReportFile",
        backref="report",
        lazy=True
    )