from app.extensions import db


class Alert(db.Model):
    """
    실시간 알림 기록
    """

    __tablename__ = "alerts"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    report_id = db.Column(
        db.BigInteger,
        db.ForeignKey("reports.id")
    )

    detection_id = db.Column(
        db.BigInteger,
        db.ForeignKey("detections.id")
    )

    alert_level = db.Column(
        db.Enum("낮음", "주의", "위험", "긴급")
    )

    message = db.Column(db.String(255))

    is_read = db.Column(db.Boolean, default=False)

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    read_at = db.Column(db.DateTime)