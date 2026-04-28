"""
회원관리(Auth) 비즈니스 로직

이 파일은 회원가입 / 로그인과 관련된 실제 처리 로직을 담당한다.

역할 예시
- 회원가입 시 username/email 중복 검사
- 비밀번호 해시 처리
- 회원 저장
- 로그인 시 아이디 또는 이메일로 사용자 조회
- 비밀번호 검증
"""

from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime
from werkzeug.security import check_password_hash
from app.repositories.role_request_repository import RoleRequestRepository
from app.repositories.user_repository import UserRepository
from app.common.exceptions import (
    ValidationException,
    UnauthorizedException,
)


class AuthService:
    """
    회원가입 / 로그인 서비스 클래스
    """

    @staticmethod
    def signup(data):
        """
        회원가입 처리

        처리 순서
        1. username 중복 확인
        2. email 중복 확인
        3. 비밀번호 해시 처리
        4. 회원 저장

        :param data: 검증된 회원가입 데이터(dict)
            예:
            {
                "username": "doha",
                "email": "doha@test.com",
                "password": "1234",
                "name": "김도하"
            }
        :return: 생성된 User 객체
        """

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        name = data.get("name")

        # -----------------------------
        # 아이디 중복 검사
        # -----------------------------
        if UserRepository.exists_by_username(username):
            raise ValidationException("이미 사용 중인 아이디입니다.")

        # -----------------------------
        # 이메일 중복 검사
        # -----------------------------
        if UserRepository.exists_by_email(email):
            raise ValidationException("이미 사용 중인 이메일입니다.")

        # -----------------------------
        # 비밀번호 해시 처리
        # -----------------------------
        # 사용자가 입력한 원문 비밀번호를 그대로 저장하면 안 된다.
        # 반드시 해시값으로 변환해서 DB에 저장해야 한다.
        password_hash = generate_password_hash(password)

        # -----------------------------
        # 사용자 저장
        # -----------------------------
        user = UserRepository.create_user(
            username=username,
            email=email,
            password_hash=password_hash,
            name=name,
            role="user"
        )

        return user

    @staticmethod
    def login(data):
        """
        로그인 처리

        login_id에는 username 또는 email 둘 다 들어올 수 있다.

        처리 순서
        1. login_id(username/email)로 사용자 조회
        2. 사용자가 없으면 로그인 실패
        3. 비밀번호 해시 비교
        4. 성공 시 사용자 반환

        :param data: 검증된 로그인 데이터(dict)
            예:
            {
                "login_id": "doha"
                "password": "1234"
            }

            또는

            {
                "login_id": "doha@test.com"
                "password": "1234"
            }

        :return: 로그인 성공한 User 객체
        """

        login_id = data.get("login_id")
        password = data.get("password")

        # -----------------------------
        # 아이디 또는 이메일로 사용자 조회
        # -----------------------------
        user = UserRepository.get_user_by_login_id(login_id)

        # 사용자가 없으면 로그인 실패
        if not user:
            raise UnauthorizedException("아이디 또는 이메일이 올바르지 않습니다.")

        # -----------------------------
        # 비밀번호 검증
        # -----------------------------
        # DB에는 password_hash만 저장되어 있기 때문에
        # check_password_hash로 입력 비밀번호와 비교해야 한다.
        if not check_password_hash(user.password_hash, password):
            raise UnauthorizedException("비밀번호가 올바르지 않습니다.")

        return user

    @staticmethod
    def get_user_info(user_id):
        """
        사용자 정보 조회

        :param user_id: 사용자 ID
        :return: User 객체
        """
        user = UserRepository.get_user_by_id(user_id)

        if not user:
            raise ValidationException("사용자 정보를 찾을 수 없습니다.")

        return user

    @staticmethod
    def request_admin_role(user_id, reason):

        RoleRequestRepository.create_request(
            user_id=user_id,
            reason=reason
        )

    @staticmethod
    def update_profile(user_id, data):
        """
        내 정보 수정 처리
        """
        user = UserRepository.get_user_by_id(user_id)

        if not user:
            raise ValidationException("사용자 정보를 찾을 수 없습니다.")

        email = data.get("email")
        name = data.get("name")

        # 이메일 중복 검사
        if email and email != user.email:
            existing_user = UserRepository.get_user_by_email(email)
            if existing_user:
                raise ValidationException("이미 사용 중인 이메일입니다.")

        updated_user = UserRepository.update_user(
            user,
            email=email,
            name=name
        )

        return updated_user

    @staticmethod
    def delete_account(user_id, password):
        """
        회원 탈퇴 처리
        비밀번호 확인 후 deleted_at에 시간 저장
        """
        user = UserRepository.get_user_by_id(user_id)

        if not user:
            raise ValidationException("사용자 정보를 찾을 수 없습니다.")

        if not password:
            raise ValidationException("비밀번호를 입력해주세요.")

        if not check_password_hash(user.password_hash, password):
            raise UnauthorizedException("비밀번호가 올바르지 않습니다.")

        deleted_user = UserRepository.soft_delete_user(
            user=user,
            deleted_at=datetime.now()
        )

        return deleted_user