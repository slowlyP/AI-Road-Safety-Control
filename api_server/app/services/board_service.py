from sqlalchemy import or_
from app.extensions import db
from app.models.board_post import BoardPost
from app.models.user_model import User


def get_board_posts(
    keyword=None,
    is_notice=None,
    user_id=None,
    writer=None,
    sort="latest"
):
    """
    게시글 전체 목록 조회
    - 삭제되지 않은 글만 조회
    - 숨김 처리되지 않은 글만 조회
    - 검색 / 공지글 / 내글 / 작성자 / 정렬 필터 적용
    """
    query = BoardPost.query.filter(
        BoardPost.deleted_at.is_(None),
        BoardPost.is_hidden.is_(False)
    )

    # 제목 + 내용 검색
    if keyword:
        like_keyword = f"%{keyword}%"
        query = query.filter(
            or_(
                BoardPost.title.like(like_keyword),
                BoardPost.content.like(like_keyword)
            )
        )

    # 공지글만 보기
    if is_notice is True:
        query = query.filter(BoardPost.is_notice.is_(True))

    # 내 글만 보기
    if user_id:
        query = query.filter(BoardPost.user_id == user_id)

    # 작성자 검색
    if writer:
        like_writer = f"%{writer}%"
        query = query.join(User, BoardPost.user_id == User.id).filter(
            or_(
                User.name.like(like_writer),
                User.username.like(like_writer)
            )
        )

    # 정렬 기준
    if sort == "oldest":
        query = query.order_by(
            BoardPost.is_notice.desc(),
            BoardPost.created_at.asc()
        )
    elif sort == "view":
        query = query.order_by(
            BoardPost.is_notice.desc(),
            BoardPost.view_count.desc(),
            BoardPost.created_at.desc()
        )
    else:
        # 기본값: 최신순
        query = query.order_by(
            BoardPost.is_notice.desc(),
            BoardPost.created_at.desc()
        )

    return query.all()


def get_board_posts_paginated(
    keyword=None,
    is_notice=None,
    user_id=None,
    writer=None,
    sort="latest",
    page=1,
    per_page=7
):
    """
    게시글 페이징 조회
    - 한 페이지당 기본 7개
    - total, page, per_page, total_pages, items 반환
    """
    query = BoardPost.query.filter(
        BoardPost.deleted_at.is_(None),
        BoardPost.is_hidden.is_(False)
    )

    # 제목 + 내용 검색
    if keyword:
        like_keyword = f"%{keyword}%"
        query = query.filter(
            or_(
                BoardPost.title.like(like_keyword),
                BoardPost.content.like(like_keyword)
            )
        )

    # 공지글만 보기
    if is_notice is True:
        query = query.filter(BoardPost.is_notice.is_(True))

    # 내 글만 보기
    if user_id:
        query = query.filter(BoardPost.user_id == user_id)

    # 작성자 검색
    if writer:
        like_writer = f"%{writer}%"
        query = query.join(User, BoardPost.user_id == User.id).filter(
            or_(
                User.name.like(like_writer),
                User.username.like(like_writer)
            )
        )

    # 정렬 기준
    if sort == "oldest":
        query = query.order_by(
            BoardPost.is_notice.desc(),
            BoardPost.created_at.asc()
        )
    elif sort == "view":
        query = query.order_by(
            BoardPost.is_notice.desc(),
            BoardPost.view_count.desc(),
            BoardPost.created_at.desc()
        )
    else:
        # 기본값: 최신순
        query = query.order_by(
            BoardPost.is_notice.desc(),
            BoardPost.created_at.desc()
        )

    # 전체 개수
    total = query.count()

    # page, per_page 보정
    if page < 1:
        page = 1

    if per_page < 1:
        per_page = 7

    # 전체 페이지 수 계산
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    # 현재 페이지가 전체 페이지보다 크면 마지막 페이지로 보정
    if page > total_pages:
        page = total_pages

    # 현재 페이지 데이터 조회
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


def get_board_post(post_id, increase_view=False):
    """
    게시글 1개 조회
    - 삭제되지 않은 글만 조회
    - increase_view=True 이면 조회수 증가
    """
    post = BoardPost.query.filter(
        BoardPost.id == post_id,
        BoardPost.deleted_at.is_(None)
    ).first()

    if not post:
        return None

    if increase_view:
        post.view_count += 1
        db.session.commit()

    return post


def create_board_post(user_id, title, content):
    """
    게시글 작성
    """
    post = BoardPost(
        user_id=user_id,
        title=title,
        content=content
    )

    db.session.add(post)
    db.session.commit()

    return post


def update_board_post(post, title, content):
    """
    게시글 수정
    """
    post.title = title
    post.content = content
    db.session.commit()

    return post


def delete_board_post(post):
    """
    게시글 삭제
    - soft delete 처리
    """
    post.deleted_at = db.func.now()
    db.session.commit()

    return post


def reset_board_post_view_count(post):
    """
    게시글 조회수 초기화
    """
    post.view_count = 0
    db.session.commit()

    return post