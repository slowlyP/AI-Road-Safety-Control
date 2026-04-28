from datetime import datetime

from app.extensions import db
from app.models.board_post import BoardPost
from app.models.board_comment import BoardComment


def get_board_comment(comment_id):
    """
    댓글 1개 조회
    - 삭제되지 않은 댓글만 조회
    """
    return BoardComment.query.filter(
        BoardComment.id == comment_id,
        BoardComment.deleted_at.is_(None)
    ).first()


def get_comment_tree_by_post(post_id):
    """
    게시글의 댓글 + 대댓글 트리 조회

    반환 형태:
    - depth=0 댓글 리스트
    - 각 댓글 객체에 reply_list 속성을 동적으로 붙여서 반환
    - 삭제/숨김 댓글은 구조 유지를 위해 남겨두고
      display_content / is_removed 값을 붙여서 템플릿에서 처리 가능하게 함
    """
    comments = BoardComment.query.filter(
        BoardComment.post_id == post_id
    ).order_by(BoardComment.created_at.asc()).all()

    comment_map = {}
    root_comments = []

    for comment in comments:
        comment.reply_list = []
        comment.is_removed = False
        comment.display_content = comment.content
        comment_map[comment.id] = comment

        if comment.deleted_at is not None:
            comment.is_removed = True
            comment.display_content = "삭제된 댓글입니다."
        elif comment.is_hidden:
            comment.is_removed = True
            comment.display_content = "숨김 처리된 댓글입니다."

    for comment in comments:
        if comment.parent_id is None or comment.depth == 0:
            root_comments.append(comment)
            continue

        parent = comment_map.get(comment.parent_id)

        if parent:
            parent.reply_list.append(comment)
        else:
            # 부모 댓글이 비정상적으로 없으면 루트로라도 보여줌
            root_comments.append(comment)

    return root_comments


def create_board_comment(user_id, post_id, content, parent_id=None):
    """
    댓글/대댓글 작성

    규칙:
    - parent_id 없으면 일반 댓글(depth=0)
    - parent_id 있으면 대댓글(depth=1)
    - 대댓글의 대댓글은 허용하지 않음
    - 부모 댓글은 같은 게시글 안에 있어야 함
    """
    content = (content or "").strip()

    if not content:
        raise ValueError("댓글 내용을 입력해주세요.")

    post = BoardPost.query.filter(
        BoardPost.id == post_id,
        BoardPost.deleted_at.is_(None)
    ).first()

    if not post:
        raise ValueError("게시글을 찾을 수 없습니다.")

    depth = 0
    parent_comment = None

    if parent_id:
        parent_comment = BoardComment.query.filter(
            BoardComment.id == parent_id,
            BoardComment.post_id == post_id,
            BoardComment.deleted_at.is_(None)
        ).first()

        if not parent_comment:
            raise ValueError("부모 댓글을 찾을 수 없습니다.")

        if parent_comment.depth != 0:
            raise ValueError("대댓글에는 다시 답글을 작성할 수 없습니다.")

        depth = 1

    comment = BoardComment(
        post_id=post_id,
        user_id=user_id,
        parent_id=parent_comment.id if parent_comment else None,
        depth=depth,
        content=content
    )

    db.session.add(comment)
    db.session.commit()

    return comment


def update_board_comment(comment, content):
    """
    댓글 수정
    """
    content = (content or "").strip()

    if not content:
        raise ValueError("댓글 내용을 입력해주세요.")

    comment.content = content
    db.session.commit()

    return comment


def delete_board_comment(comment):
    """
    댓글 삭제
    - soft delete
    - 내용은 남겨두고 deleted_at만 기록
    - 템플릿에서는 '삭제된 댓글입니다.' 로 표시 가능
    """
    comment.deleted_at = datetime.utcnow()
    db.session.commit()

    return comment


def can_manage_board_comment(comment, user_id=None, is_admin=False):
    """
    댓글 수정/삭제 권한 체크
    - 관리자면 가능
    - 아니면 작성자 본인만 가능
    """
    if is_admin:
        return True

    if not user_id:
        return False

    return comment.user_id == user_id