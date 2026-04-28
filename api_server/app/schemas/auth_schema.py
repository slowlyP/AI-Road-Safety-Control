# 회원관리에서 들어오는 요청 데이터를 검증

# ex)
# 회원가입 요청 데이터 검증
# 로그인 요청 데이터 검증

# 사용자가 보낸 JSON이 이런 형태인지 확인

"""
회원관리(Auth) 관련 요청 데이터 검증 스키마

이 파일에서는 회원가입, 로그인 요청 시
사용자가 보낸 데이터를 검증한다.
"""

from marshmallow import Schema, fields, validate, validates, ValidationError

class SignupSchema(Schema):
    """
    회원가입 요청 데이터 검증 스키마

    검증 대상 예시:
    {
        "username": "doha",
        "email": "doha@test.com",
        "password": "1234",
        "name": "김도하"
    }
    """

    # 아이디
    username = fields.Str(
        required=True,
        error_messages={"required": "아이디는 필수 입력값입니다."},
        validate=validate.Length(
            min=4,
            max=50,
            error="아이디는 4자 이상 50자 이하로 입력해주세요."
        )
    )

    # 이메일
    email = fields.Email(
        required=True,
        error_messages={
            "required": "이메일은 필수 입력값입니다.",
            "invalid": "올바른 이메일 형식이 아닙니다."
        }
    )

    # 비밀번호
    password = fields.Str(
        required=True,
        error_messages={"required": "비밀번호는 필수 입력값입니다."},
        validate=validate.Length(
            min=4,
            max=255,
            error="비밀번호는 4자 이상 입력해주세요."
        )
    )

    # 이름
    name = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(
            max=50,
            error="이름은 50자 이하로 입력해주세요."
        )
    )

    @validates("username")
    def validate_username_space(self, value, **kwargs):
        """
        아이디 공백 검사
        """
        if " " in value:
            raise ValidationError("아이디에는 공백을 포함할 수 없습니다.")

class LoginSchema(Schema):
    """
    로그인 요청 데이터 검증 스키마

    login_id에는 아이디(username) 또는 이메일(email)을 입력할 수 있다.

    검증 대상 예시:
    {
        "login_id": "doha",
        "password": "1234"
    }

    또는

    {
        "login_id": "doha@test.com",
        "password": "1234"
    }
    """

    # 아이디 또는 이메일
    login_id = fields.Str(
        required=True,
        error_messages={"required": "아이디 또는 이메일은 필수 입력값입니다."}
    )

    # 비밀번호
    password = fields.Str(
        required=True,
        error_messages={"required": "비밀번호는 필수 입력값입니다."}
    )