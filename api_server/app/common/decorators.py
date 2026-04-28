# 로그인 여부나 관리자 권한 체크할 때 쓰는 데코레이터

from functools import wraps
from flask import request, session, redirect, url_for, flash
from app.common.response import error_response


def _is_api_request():
    """
    현재 요청이 API / AJAX 계열인지 판별

    기준
    1) /api 로 시작
    2) 실시간 알림 관련 관리자 API
    3) AJAX 요청 헤더 존재
    """
    if request.path.startswith("/api"):
        return True

    if request.path.startswith("/admin/realtime-alerts"):
        return True

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return True

    return False


def login_required(func):
    """
    로그인 여부 확인용 데코레이터

    현재 프로젝트 기준:
    - session["user_id"] 존재 여부로 로그인 판단
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            # API 요청이면 JSON 에러 반환
            if _is_api_request():
                return error_response(
                    message="로그인이 필요합니다.",
                    status_code=401
                )

            # 일반 페이지 요청이면 로그인 페이지로 이동
            return redirect(url_for("auth.login"))

        return func(*args, **kwargs)

    return wrapper


def admin_required(func):
    """
    관리자 권한 체크용 데코레이터

    현재 프로젝트 기준:
    - session["role"] == "admin"
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            # API 요청이면 JSON 에러 반환
            if _is_api_request():
                return error_response(
                    message="관리자 권한이 필요합니다.",
                    status_code=403
                )

            # 일반 페이지 요청이면 메인으로 이동
            flash("관리자만 접근할 수 있습니다.", "danger")
            return redirect(url_for("main.index"))

        return func(*args, **kwargs)

    return wrapper