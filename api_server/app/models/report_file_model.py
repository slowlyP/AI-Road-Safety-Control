from app.extensions import db


class ReportFile(db.Model):
    """
    신고 첨부 파일
    """

    __tablename__ = "report_files"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    report_id = db.Column(
        db.BigInteger,
        db.ForeignKey("reports.id"),
        nullable=False
    )

    original_name = db.Column(db.String(255), nullable=False)

    stored_name = db.Column(db.String(255), nullable=False)

    file_path = db.Column(db.String(500), nullable=False)

    file_type = db.Column(
        db.Enum("이미지", "영상"),
        nullable=False
    )

    file_size = db.Column(db.BigInteger)

    is_active = db.Column(db.Boolean, default=True)

    uploaded_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    deleted_at = db.Column(db.DateTime)