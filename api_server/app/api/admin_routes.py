"""
관리자 대시보드 라우트
"""

from flask import Blueprint, render_template, session, redirect, url_for, flash

from app.services.admin_service import AdminService


admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


def _check_admin():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "admin":
        flash("관리자만 접근할 수 있습니다.", "danger")
        return redirect(url_for("main.index"))

    return None


@admin_bp.route("/dashboard", methods=["GET"])
@admin_bp.route("/dashboard/", methods=["GET"])
def dashboard():
    """
    관리자 대시보드 페이지
    """

    check = _check_admin()
    if check:
        return check

    stats = AdminService.get_dashboard_stats()

    return render_template(
        "admin/dashboard.html",
        stats=stats
    )