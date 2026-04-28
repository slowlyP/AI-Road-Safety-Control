"""
회원관리(Auth) 라우트

이 파일은 회원가입 / 로그인 / 로그아웃 / 마이페이지 / 관리자 권한 신청 관련
HTTP 요청을 처리한다.

주요 기능
- GET /auth/login         : 로그인 페이지 반환
- POST /auth/login        : 로그인 처리
- GET /auth/signup        : 회원가입 페이지 반환
- POST /auth/signup       : 회원가입 처리
- GET /auth/logout        : 로그아웃
- GET /auth/mypage        : 마이페이지
- GET /auth/role-request  : 관리자 권한 신청 페이지
- POST /auth/role-request : 관리자 권한 신청 처리
"""

from flask import Blueprint, render_template, request, session, redirect, url_for
from marshmallow import ValidationError

from app.schemas.auth_schema import SignupSchema, LoginSchema
from app.services.auth_service import AuthService
from app.common.response import success_response, error_response
from app.common.exceptions import BaseCustomException
from app.repositories.user_repository import UserRepository

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    로그인 페이지 / 로그인 처리
    """

    if request.method == "GET":
        return render_template("auth/login.html")

    try:
        request_data = request.get_json()

        if not request_data:
            return error_response(
                message="요청 데이터가 없습니다.",
                status_code=400
            )

        validated_data = LoginSchema().load(request_data)
        user = AuthService.login(validated_data)

        # 세션 저장
        session["user_id"] = user.id
        session["username"] = user.username
        session["email"] = user.email
        session["name"] = user.name
        session["role"] = user.role

        return success_response(
            message="로그인에 성공했습니다.",
            data={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "role": user.role
            },
            status_code=200
        )

    except ValidationError as e:
        return error_response(
            message="입력값 검증 실패",
            errors=e.messages,
            status_code=400
        )

    except BaseCustomException as e:
        return error_response(
            message=e.message,
            status_code=e.status_code
        )

    except Exception as e:
        return error_response(
            message="로그인 처리 중 서버 오류가 발생했습니다.",
            errors=str(e),
            status_code=500
        )


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    """
    회원가입 페이지 / 회원가입 처리
    """

    if request.method == "GET":
        return render_template("auth/signup.html")

    try:
        request_data = request.get_json()

        if not request_data:
            return error_response(
                message="요청 데이터가 없습니다.",
                status_code=400
            )

        validated_data = SignupSchema().load(request_data)
        user = AuthService.signup(validated_data)

        return success_response(
            message="회원가입이 완료되었습니다.",
            data={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "role": user.role
            },
            status_code=201
        )

    except ValidationError as e:
        return error_response(
            message="입력값 검증 실패",
            errors=e.messages,
            status_code=400
        )

    except BaseCustomException as e:
        return error_response(
            message=e.message,
            status_code=e.status_code
        )

    except Exception as e:
        return error_response(
            message="회원가입 처리 중 서버 오류가 발생했습니다.",
            errors=str(e),
            status_code=500
        )


@auth_bp.route("/logout", methods=["GET"])
def logout():
    """
    로그아웃 처리
    """

    session.clear()
    return redirect(url_for("main.index"))


@auth_bp.route("/role-request", methods=["GET", "POST"])
def role_request():
    """
    관리자 권한 신청 페이지 / 신청 처리
    """

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = UserRepository.get_user_by_id(session["user_id"])

    if request.method == "GET":
        return render_template(
            "auth/role_request.html",
            user=user
        )

    try:
        request_data = request.get_json()

        if not request_data:
            return error_response(
                message="요청 데이터가 없습니다.",
                status_code=400
            )

        reason = request_data.get("request_reason")

        AuthService.request_admin_role(
            user_id=session["user_id"],
            reason=reason
        )

        return success_response(
            message="관리자 권한 신청이 완료되었습니다.",
            status_code=201
        )

    except BaseCustomException as e:
        return error_response(
            message=e.message,
            status_code=e.status_code
        )

    except Exception as e:
        return error_response(
            message="권한 신청 처리 중 서버 오류가 발생했습니다.",
            errors=str(e),
            status_code=500
        )

@auth_bp.route("/update-profile", methods=["GET", "POST"])
def update_profile():
    """
    내 정보 수정 페이지 / 수정 처리
    """
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = UserRepository.get_user_by_id(session["user_id"])

    if request.method == "GET":
        return render_template("auth/edit_profile.html", user=user)

    try:
        request_data = request.get_json()

        if not request_data:
            return error_response(
                message="요청 데이터가 없습니다.",
                status_code=400
            )

        updated_user = AuthService.update_profile(
            user_id=session["user_id"],
            data=request_data
        )

        return success_response(
            message="내 정보가 수정되었습니다.",
            data={
                "id": updated_user.id,
                "username": updated_user.username,
                "email": updated_user.email,
                "name": updated_user.name,
                "role": updated_user.role
            },
            status_code=200
        )

    except BaseCustomException as e:
        return error_response(
            message=e.message,
            status_code=e.status_code
        )

    except Exception as e:
        return error_response(
            message="내 정보 수정 중 서버 오류가 발생했습니다.",
            errors=str(e),
            status_code=500
        )


@auth_bp.route("/delete-account", methods=["GET", "POST"])
def delete_account():
    """
    회원 탈퇴 페이지 / 탈퇴 처리
    """
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = UserRepository.get_user_by_id(session["user_id"])

    if request.method == "GET":
        return render_template(
            "auth/delete_account.html",
            user=user
        )

    try:
        request_data = request.get_json()

        if not request_data:
            return error_response(
                message="요청 데이터가 없습니다.",
                status_code=400
            )

        password = request_data.get("password")

        AuthService.delete_account(
            user_id=session["user_id"],
            password=password
        )

        session.clear()

        return success_response(
            message="회원 탈퇴가 완료되었습니다.",
            status_code=200
        )

    except BaseCustomException as e:
        return error_response(
            message=e.message,
            status_code=e.status_code
        )

    except Exception as e:
        return error_response(
            message="회원 탈퇴 중 서버 오류가 발생했습니다.",
            errors=str(e),
            status_code=500
        )