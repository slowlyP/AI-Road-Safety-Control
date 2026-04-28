# models 폴더의 역할
# models = DB 테이블을 Python 코드로 정의하는 곳


from app.extensions import db


class User(db.Model):
    """
    users 테이블
    기능: 회원 정보 및 권한 관리
    """

    __tablename__ = "users"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    username = db.Column(db.String(50), unique=True, nullable=False)

    email = db.Column(db.String(100), unique=True, nullable=False)

    password_hash = db.Column(db.String(255), nullable=False)

    name = db.Column(db.String(50))

    role = db.Column(db.Enum("user", "admin"), default="user")

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    updated_at = db.Column(db.DateTime)

    deleted_at = db.Column(db.DateTime)