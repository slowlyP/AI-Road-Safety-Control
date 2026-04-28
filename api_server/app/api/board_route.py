from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort

from app.services.board_service import (
    get_board_posts_paginated,
    get_board_post,
    create_board_post,
    update_board_post,
    delete_board_post,
    reset_board_post_view_count,
)

from app.services.board_comment_service import (
    get_board_comment,
    get_comment_tree_by_post,
    create_board_comment,
    delete_board_comment,
    can_manage_board_comment,
)

board_bp = Blueprint("board", __name__, url_prefix="/board")


@board_bp.route("/", methods=["GET"])
def board_list():
    """
    🔹 자유게시판 목록 + 필터 + 페이징

    기능:
    - 검색어 (제목 + 내용)
    - 공지글 필터
    - 내 글 필터
    - 작성자 검색
    - 정렬 (최신순 / 과거순 / 조회순)
    - 페이지네이션 처리 (한 페이지 7개)
    """

    # 🔹 검색어
    keyword = request.args.get("keyword", "").strip()

    # 🔹 공지글 필터 (1이면 공지글만)
    notice = request.args.get("notice", "").strip()
    is_notice = True if notice == "1" else None

    # 🔹 내 글 필터 (로그인 사용자 기준)
    my = request.args.get("my", "").strip()
    my_user_id = session.get("user_id") if my == "1" and session.get("user_id") else None

    # 🔹 작성자 검색
    writer = request.args.get("writer", "").strip()

    # 🔹 정렬 기준
    sort = request.args.get("sort", "latest").strip()
    if sort not in ["latest", "oldest", "view"]:
        sort = "latest"

    # 🔹 현재 페이지 번호
    page = request.args.get("page", 1, type=int)

    # 🔹 페이지당 게시글 개수 (🔥 중요: 7개로 변경)
    per_page = 7

    # 🔹 서비스에서 페이징 데이터 조회
    result = get_board_posts_paginated(
        keyword=keyword,
        is_notice=is_notice,
        user_id=my_user_id,
        writer=writer,
        sort=sort,
        page=page,
        per_page=per_page
    )

    # 🔹 템플릿으로 전달
    return render_template(
        "board/list.html",
        posts=result["items"],         # 현재 페이지 데이터
        total=result["total"],         # 전체 게시글 수
        page=result["page"],           # 현재 페이지
        per_page=result["per_page"],   # 페이지당 개수 (7)
        total_pages=result["total_pages"],  # 전체 페이지 수
        keyword=keyword,
        notice=notice,
        my=my,
        writer=writer,
        sort=sort
    )


@board_bp.route("/<int:post_id>", methods=["GET"])
def board_detail(post_id):
    """
    🔹 게시글 상세
    - 조회수 증가
    - 댓글/대댓글 트리 조회
    """
    post = get_board_post(post_id=post_id, increase_view=True)

    if not post:
        abort(404)

    comments = get_comment_tree_by_post(post_id=post.id)

    return render_template(
        "board/detail.html",
        post=post,
        comments=comments
    )


@board_bp.route("/create", methods=["GET", "POST"])
def board_create():
    """
    🔹 게시글 작성
    - 로그인 사용자만 가능
    """
    if not session.get("user_id"):
        flash("로그인 후 글을 작성할 수 있습니다.", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        # 🔹 제목 검증
        if not title:
            flash("제목을 입력해주세요.", "warning")
            return render_template("board/create.html", title=title, content=content)

        # 🔹 내용 검증
        if not content:
            flash("내용을 입력해주세요.", "warning")
            return render_template("board/create.html", title=title, content=content)

        # 🔹 게시글 생성
        post = create_board_post(
            user_id=session.get("user_id"),
            title=title,
            content=content
        )

        flash("게시글이 등록되었습니다.", "success")
        return redirect(url_for("board.board_detail", post_id=post.id))

    return render_template("board/create.html")


@board_bp.route("/<int:post_id>/edit", methods=["GET", "POST"])
def board_edit(post_id):
    """
    🔹 게시글 수정
    - 작성자 본인만 가능
    """
    if not session.get("user_id"):
        flash("로그인 후 이용할 수 있습니다.", "warning")
        return redirect(url_for("auth.login"))

    post = get_board_post(post_id=post_id, increase_view=False)

    if not post:
        abort(404)

    # 🔹 작성자 체크
    if post.user_id != session.get("user_id"):
        flash("본인이 작성한 글만 수정할 수 있습니다.", "danger")
        return redirect(url_for("board.board_detail", post_id=post.id))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        if not title:
            flash("제목을 입력해주세요.", "warning")
            return render_template("board/edit.html", post=post)

        if not content:
            flash("내용을 입력해주세요.", "warning")
            return render_template("board/edit.html", post=post)

        update_board_post(post, title, content)

        flash("게시글이 수정되었습니다.", "success")
        return redirect(url_for("board.board_detail", post_id=post.id))

    return render_template("board/edit.html", post=post)


@board_bp.route("/<int:post_id>/delete", methods=["POST"])
def board_delete(post_id):
    """
    🔹 게시글 삭제
    - 작성자 본인만 가능
    """
    if not session.get("user_id"):
        flash("로그인 후 이용할 수 있습니다.", "warning")
        return redirect(url_for("auth.login"))

    post = get_board_post(post_id=post_id, increase_view=False)

    if not post:
        abort(404)

    if post.user_id != session.get("user_id"):
        flash("본인이 작성한 글만 삭제할 수 있습니다.", "danger")
        return redirect(url_for("board.board_detail", post_id=post.id))

    delete_board_post(post)

    flash("게시글이 삭제되었습니다.", "success")
    return redirect(url_for("board.board_list"))


@board_bp.route("/<int:post_id>/reset-view", methods=["POST"])
def board_reset_view(post_id):
    """
    🔹 조회수 초기화 (관리자만)
    """
    if not session.get("user_id"):
        flash("로그인 후 이용할 수 있습니다.", "warning")
        return redirect(url_for("auth.login"))

    if session.get("role") != "admin":
        flash("조회수 초기화는 관리자만 가능합니다.", "danger")
        return redirect(url_for("board.board_detail", post_id=post_id))

    post = get_board_post(post_id=post_id, increase_view=False)

    if not post:
        abort(404)

    reset_board_post_view_count(post)

    flash("조회수가 초기화되었습니다.", "success")
    return redirect(url_for("board.board_detail", post_id=post.id))


@board_bp.route("/<int:post_id>/comments/create", methods=["POST"])
def board_comment_create(post_id):
    """
    🔹 댓글 / 대댓글 작성
    """
    if not session.get("user_id"):
        flash("로그인 후 댓글을 작성할 수 있습니다.", "warning")
        return redirect(url_for("auth.login"))

    content = request.form.get("content", "").strip()
    parent_id = request.form.get("parent_id", "").strip()

    try:
        parent_id = int(parent_id) if parent_id else None

        create_board_comment(
            user_id=session.get("user_id"),
            post_id=post_id,
            content=content,
            parent_id=parent_id
        )

        flash("댓글이 등록되었습니다.", "success")

    except ValueError as e:
        flash(str(e), "warning")
    except Exception:
        flash("댓글 등록 중 오류가 발생했습니다.", "danger")

    return redirect(url_for("board.board_detail", post_id=post_id))


@board_bp.route("/comments/<int:comment_id>/delete", methods=["POST"])
def board_comment_delete(comment_id):
    """
    🔹 댓글 삭제
    - 작성자 또는 관리자만 가능
    """
    if not session.get("user_id"):
        flash("로그인 후 이용할 수 있습니다.", "warning")
        return redirect(url_for("auth.login"))

    comment = get_board_comment(comment_id)

    if not comment:
        abort(404)

    is_admin = session.get("role") == "admin"

    if not can_manage_board_comment(
        comment=comment,
        user_id=session.get("user_id"),
        is_admin=is_admin
    ):
        flash("댓글을 삭제할 권한이 없습니다.", "danger")
        return redirect(url_for("board.board_detail", post_id=comment.post_id))

    delete_board_comment(comment)

    flash("댓글이 삭제되었습니다.", "success")
    return redirect(url_for("board.board_detail", post_id=comment.post_id))