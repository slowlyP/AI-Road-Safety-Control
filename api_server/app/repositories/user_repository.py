"""
사용자(User) 관련 DB 접근 로직

이 파일은 users 테이블에 직접 접근하는 역할을 한다.
즉, 회원 정보를 조회/저장/수정할 때
실제 DB 쿼리를 담당하는 계층이다.

역할 예시
- username 중복 확인
- email 중복 확인
- 회원 저장
- 아이디(username) 또는 이메일(email)로 회원 조회
"""

from sqlalchemy import or_

from app.extensions import db
from app.models.user_model import User


class UserRepository:
    """
    사용자 관련 DB 처리 클래스
    """

    @staticmethod
    def create_user(username, email, password_hash, name=None, role="user"):
        """
        회원 생성

        회원가입 시 새로운 사용자를 users 테이블에 저장한다.

        :param username: 사용자 아이디
        :param email: 사용자 이메일
        :param password_hash: 해시 처리된 비밀번호
        :param name: 사용자 이름
        :param role: 권한 (기본값: user)
        :return: 저장된 User 객체
        """
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            name=name,
            role=role
        )

        db.session.add(user)
        db.session.commit()

        return user

    @staticmethod
    def get_user_by_id(user_id):
        """
        사용자 ID로 회원 1명 조회

        :param user_id: users.id
        :return: User 객체 또는 None
        """
        return User.query.filter_by(id=user_id, deleted_at=None).first()

    @staticmethod
    def get_user_by_username(username):
        """
        username으로 회원 조회

        :param username: 사용자 아이디
        :return: User 객체 또는 None
        """
        return User.query.filter_by(username=username, deleted_at=None).first()

    @staticmethod
    def get_user_by_email(email):
        """
        email로 회원 조회

        :param email: 사용자 이메일
        :return: User 객체 또는 None
        """
        return User.query.filter_by(email=email, deleted_at=None).first()

    @staticmethod
    def get_user_by_login_id(login_id):
        """
        로그인용 사용자 조회

        login_id에는 username 또는 email이 들어올 수 있다.
        즉, 아이디 로그인 / 이메일 로그인 둘 다 지원하기 위한 메서드다.

        :param login_id: username 또는 email
        :return: User 객체 또는 None
        """
        return User.query.filter(
            User.deleted_at.is_(None),
            or_(
                User.username == login_id,
                User.email == login_id
            )
        ).first()

    @staticmethod
    def exists_by_username(username):
        """
        username 중복 여부 확인

        :param username: 사용자 아이디
        :return: True / False
        """
        return User.query.filter_by(username=username, deleted_at=None).first() is not None

    @staticmethod
    def exists_by_email(email):
        """
        email 중복 여부 확인

        :param email: 사용자 이메일
        :return: True / False
        """
        return User.query.filter_by(email=email, deleted_at=None).first() is not None

    @staticmethod
    def get_all_users():
        """
        전체 회원 목록 조회
        (삭제되지 않은 회원만 조회)

        :return: User 객체 리스트
        """
        return User.query.filter_by(deleted_at=None).order_by(User.id.desc()).all()

    @staticmethod
    def update_user(user, **kwargs):
        """
        회원 정보 수정

        수정할 값을 kwargs로 받아서 User 객체에 반영한다.

        사용 예:
        UserRepository.update_user(user, name="김도하", role="admin")

        :param user: 수정할 User 객체
        :param kwargs: 수정할 필드 값
        :return: 수정된 User 객체
        """
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        db.session.commit()
        return user

    @staticmethod
    def soft_delete_user(user, deleted_at):
        """
        회원 소프트 삭제

        실제 DB 레코드를 지우지 않고 deleted_at 값을 넣어
        삭제 처리한다.

        :param user: 삭제할 User 객체
        :param deleted_at: 삭제 시각(datetime)
        :return: 삭제 처리된 User 객체
        """
        user.deleted_at = deleted_at
        db.session.commit()
        return user