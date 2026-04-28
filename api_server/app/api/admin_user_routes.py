"""
관리자 회원 관리 라우트
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from app.services.admin_user_service import AdminUserService


admin_user_bp = Blueprint(
    "admin_user",
    __name__,
    url_prefix="/admin/users"
)


def _check_admin():
    """
    관리자 접근 체크
    """
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "admin":
        flash("관리자만 접근할 수 있습니다.", "danger")
        return redirect(url_for("main.index"))

    return None


@admin_user_bp.route("/", methods=["GET"])
def user_list():
    """
    관리자 회원 목록 페이지
    """

    check = _check_admin()
    if check:
        return check

    page = request.args.get("page", 1, type=int)
    keyword = request.args.get("keyword", "", type=str)
    role = request.args.get("role", "", type=str)

    service = AdminUserService()
    result = service.get_user_list(
        page=page,
        per_page=10,
        keyword=keyword,
        role=role
    )

    return render_template(
        "admin/users/list.html",
        users=result["users"],
        pagination=result["pagination"],
        keyword=keyword,
        role=role
    )


@admin_user_bp.route("/role-requests", methods=["GET"])
def role_request_list():
    """
    관리자 권한 신청 목록 페이지
    """

    check = _check_admin()
    if check:
        return check

    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "", type=str)
    keyword = request.args.get("keyword", "", type=str)

    service = AdminUserService()
    result = service.get_role_request_list(
        page=page,
        per_page=10,
        status=status,
        keyword=keyword
    )

    return render_template(
        "admin/users/role_requests.html",
        requests=result["requests"],
        pagination=result["pagination"],
        status=status,
        keyword=keyword
    )


@admin_user_bp.route("/role-requests/<int:request_id>/review", methods=["POST"])
def review_role_request(request_id):
    """
    관리자 권한 신청 승인 / 거절
    """

    check = _check_admin()
    if check:
        return check

    status = request.form.get("status")
    admin_id = session.get("user_id")

    service = AdminUserService()

    try:
        service.review_role_request(request_id, admin_id, status)
        flash("권한 신청이 처리되었습니다.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("admin_user.role_request_list"))


@admin_user_bp.route("/<int:user_id>", methods=["GET"])
def user_detail(user_id):
    """
    관리자 회원 상세 페이지
    """

    check = _check_admin()
    if check:
        return check

    service = AdminUserService()

    try:
        user_data = service.get_user_detail(user_id)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("admin_user.user_list"))

    return render_template(
        "admin/users/detail.html",
        user=user_data["user"],
        role_requests=user_data["role_requests"],
        reports=user_data["reports"]
    )


@admin_user_bp.route("/<int:user_id>/role", methods=["POST"])
def update_user_role(user_id):
    """
    회원 권한 변경
    """

    check = _check_admin()
    if check:
        return check

    new_role = request.form.get("role")
    admin_id = session.get("user_id")

    service = AdminUserService()

    try:
        service.update_user_role(user_id, new_role, admin_id)
        flash("회원 권한이 변경되었습니다.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("admin_user.user_detail", user_id=user_id))


@admin_user_bp.route("/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    """
    관리자 회원 삭제 (soft delete)
    """

    check = _check_admin()
    if check:
        return check

    admin_id = session.get("user_id")
    service = AdminUserService()

    try:
        service.delete_user(user_id, admin_id)
        flash("회원이 삭제되었습니다.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("admin_user.user_list"))