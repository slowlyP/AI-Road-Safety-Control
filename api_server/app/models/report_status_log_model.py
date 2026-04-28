from app.extensions import db


class ReportStatusLog(db.Model):

    __tablename__ = "report_status_logs"

    id = db.Column(db.BigInteger, primary_key=True)

    report_id = db.Column(
        db.BigInteger,
        db.ForeignKey("reports.id"),
        nullable=False
    )

    old_status = db.Column(
        db.Enum("접수", "확인중", "처리완료", "오탐"),
        nullable=True
    )

    new_status = db.Column(
        db.Enum("접수", "확인중", "처리완료", "오탐"),
        nullable=False
    )

    changed_by = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id"),
        nullable=True
    )

    memo = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, nullable=False)