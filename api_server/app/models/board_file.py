from datetime import datetime
from app.extensions import db


class BoardFile(db.Model):
    __tablename__ = "board_files"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    post_id = db.Column(
        db.BigInteger,
        db.ForeignKey("board_posts.id"),
        nullable=False
    )

    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.Enum("이미지", "영상"), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    deleted_at = db.Column(db.DateTime, nullable=True)

    post = db.relationship(
        "BoardPost",
        backref=db.backref("files", lazy="dynamic")
    )

    def __repr__(self):
        return f"<BoardFile id={self.id} post_id={self.post_id} type={self.file_type}>"