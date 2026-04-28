from datetime import datetime
from app.extensions import db


class BoardPost(db.Model):
    __tablename__ = "board_posts"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    # 작성자
    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # 게시글 기본 정보
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)

    # 부가 정보
    view_count = db.Column(db.Integer, nullable=False, default=0)
    is_notice = db.Column(db.Boolean, nullable=False, default=False)
    is_hidden = db.Column(db.Boolean, nullable=False, default=False)

    # 시간 정보
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    deleted_at = db.Column(db.DateTime, nullable=True)

    # 작성자 관계
    user = db.relationship("User", backref=db.backref("board_posts", lazy="dynamic"))

    def __repr__(self):
        return f"<BoardPost id={self.id} title={self.title}>"