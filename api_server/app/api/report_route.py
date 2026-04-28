from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, current_app
from app.services.report_service import ReportService
# 공통 응답 함수 import
from app.common.response import success_response, error_response

# Blueprint 생성
report_bp = Blueprint('report', __name__)


class ReportRoute:
    """
    신고 관련 HTTP 요청(Route)을 처리하는 클래스
    """

    # GET /report/create 페이지 라우트는 프론트엔드 서버(React)로 이관되었습니다.
    # API 서버는 순수 JSON 응답만 처리합니다.

    @staticmethod
    @report_bp.route('/api/report', methods=['POST'])
    def create_report():

        current_user_id = session.get('user_id')

        if not current_user_id:
            return error_response(
                message="로그인이 필요한 서비스 입니다.",
                status_code=401
            )

        try:
            # 데이터 및 파일 수신
            form_data = request.form
            upload_file = request.files.get('files')

            # 파일 유효성 검사
            if not upload_file or upload_file.filename == '':
                return error_response(
                    message="첨부된 파일이 없습니다.",
                    status_code=400
                )

            # 서비스 레이어 호출 (YOLO 분석 및 DB 저장)
            result = ReportService.process_report_submission(
                current_user_id,
                form_data,
                upload_file
            )

            # 성공 시 결과 반환 (함수 종료 지점)
            return success_response(
                data=result,
                message="신고가 성공적으로 접수되었습니다."
            )


        except ValueError as ve:
            # 파일 형식 오류 등 비즈니스 로직 에러 처리
            return error_response(
                message=str(ve),
                status_code=400
            )

        except Exception as e:
            # 예상치 못한 시스템 에러 처리
            print(f"Route Error: {e}")
            return error_response(
                message="신고 접수 중 서버 오류가 발생했습니다.",
                status_code=500
            )