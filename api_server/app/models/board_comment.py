from datetime import datetime
from app.extensions import db


class BoardComment(db.Model):
    __tablename__ = "board_comments"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    # 어떤 게시글의 댓글인지
    post_id = db.Column(
        db.BigInteger,
        db.ForeignKey("board_posts.id"),
        nullable=False
    )

    # 작성자
    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # 대댓글용 부모 댓글 ID
    # 원댓글이면 NULL
    parent_id = db.Column(
        db.BigInteger,
        db.ForeignKey("board_comments.id"),
        nullable=True
    )

    # 0 = 댓글, 1 = 대댓글
    depth = db.Column(db.SmallInteger, nullable=False, default=0)

    # 댓글 내용
    content = db.Column(db.Text, nullable=False)

    # 숨김 / 삭제 처리
    is_hidden = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    deleted_at = db.Column(db.DateTime, nullable=True)

    # 관계 설정
    post = db.relationship(
        "BoardPost",
        backref=db.backref("comments", lazy="dynamic")
    )

    user = db.relationship(
        "User",
        backref=db.backref("board_comments", lazy="dynamic")
    )

    parent = db.relationship(
        "BoardComment",
        remote_side=[id],
        backref=db.backref("children", lazy="dynamic")
    )

    def __repr__(self):
        return f"<BoardComment id={self.id} post_id={self.post_id} depth={self.depth}>"