# 프로젝트 내부 로직에서 사용할 예외 정의
# 공통 예외 클래스를 만드는 파일
# ex) 로그인 실패, 권한 없음, 데이터 없음, 입력 오류 등

class BaseCustomException(Exception):
    """
    모든 커스텀 예외의 부모 클래스
    """

    def __init__(self, message="에러가 발생했습니다.", status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationException(BaseCustomException):
    """
    입력값 검증 실패
    """
    def __init__(self, message="입력값이 올바르지 않습니다."):
        super().__init__(message=message, status_code=400)


class UnauthorizedException(BaseCustomException):
    """
    로그인/인증 실패
    """
    def __init__(self, message="인증이 필요합니다."):
        super().__init__(message=message, status_code=401)


class ForbiddenException(BaseCustomException):
    """
    권한 없음
    """
    def __init__(self, message="접근 권한이 없습니다."):
        super().__init__(message=message, status_code=403)


class NotFoundException(BaseCustomException):
    """
    데이터 없음
    """
    def __init__(self, message="데이터를 찾을 수 없습니다."):
        super().__init__(message=message, status_code=404)