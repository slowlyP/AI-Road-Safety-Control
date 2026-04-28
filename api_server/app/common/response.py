# API 응답 형식을 통한 파일

# 예를 들어 앞으로 회원가입, 로그인, 신고등록 API에서
# 응답을 전부 이런 식으로 통일

# {
#   "success": true,
#   "message": "회원가입 성공",
#   "data": {...}
# }
#----------------------------------------------

from flask import jsonify


def success_response(message="요청 성공", data=None, status_code=200):
    """
    성공 응답 공통 함수

    :param message: 응답 메시지
    :param data: 실제 반환 데이터
    :param status_code: HTTP 상태 코드
    """
    response = {
        "success": True,
        "message": message,
        "data": data
    }
    return jsonify(response), status_code


def error_response(message="요청 실패", errors=None, status_code=400):
    """
    실패 응답 공통 함수

    :param message: 에러 메시지
    :param errors: 상세 에러 내용
    :param status_code: HTTP 상태 코드
    """
    response = {
        "success": False,
        "message": message,
        "errors": errors
    }
    return jsonify(response), status_code
