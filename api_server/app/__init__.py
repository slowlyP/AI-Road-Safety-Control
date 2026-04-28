"""
Flask 애플리케이션을 생성하는 파일
"""

from flask import Flask, session, request
from werkzeug.exceptions import RequestEntityTooLarge
from flask_cors import CORS

from .config import Config
from .extensions import db, migrate, socketio
from app.common.response import error_response



def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )
    
    CORS(app, supports_credentials=True)

    # -------------------------------------------------
    # 앱 설정 로드
    # -------------------------------------------------
    app.config.from_object(Config)

    # -------------------------------------------------
    # 전역 업로드 용량 초과(413) 처리
    # - Config.MAX_CONTENT_LENGTH를 초과하면 여기로 떨어짐
    # -------------------------------------------------
    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_too_large(e):
        return error_response(
            message="업로드 가능한 최대 용량(50MB)을 초과했습니다.",
            status_code=413
        )

    # -------------------------------------------------
    # Flask 확장 초기화
    # -------------------------------------------------
    # DB 초기화
    db.init_app(app)

    # migration 초기화
    migrate.init_app(app, db)

    # 소켓 초기화
    socketio.init_app(app)

    # -------------------------------------------------
    # 모델 로딩
    # - SQLAlchemy가 모델을 인식할 수 있도록 앱 컨텍스트 안에서 import
    # -------------------------------------------------
    with app.app_context():
        from . import models

    # -----------------------------
    # 템플릿 공통 변수 주입
    # -----------------------------
    @app.context_processor
    def inject_user_state():
        """
        모든 템플릿에서 로그인 상태 / 관리자 여부를 공통으로 사용하기 위한 값 주입

        base.html 에서 사용 예:
        {% if is_logged_in and is_admin %}
            실시간 알림 CSS / JS / 오디오 / 토스트 영역 로드
        {% endif %}

        모든 템플릿에서 로그인 상태 / 관리자 여부 / 관리자 사이드바 카운트를 공통 사용
        """
        is_logged_in = "user_id" in session
        is_admin = session.get("role") == "admin"
        user_name = session.get("name")

        admin_pending_report_count = 0
        admin_pending_role_count = 0

        if is_admin:
            from app.models.report_model import Report
            from app.models.role_request_model import RoleRequest

            admin_pending_report_count = Report.query.filter(
                Report.deleted_at.is_(None),
                Report.status == "접수"
            ).count()

            admin_pending_role_count = RoleRequest.query.filter(
                RoleRequest.status == "대기"
            ).count()

        endpoint = request.endpoint or ""
        active_member = None

        if endpoint.startswith("main."):
            active_member = "kdh"
        elif endpoint.startswith("report."):
            active_member = "smg"
        elif endpoint.startswith("report_list."):
            active_member = "lhj"
        elif endpoint.startswith("realtime_monitor."):
            active_member = "kdk"
        elif endpoint.startswith("admin_realtime_alert."):
            active_member = "kdk"
        elif endpoint.startswith("admin."):
            active_member = "kdh"

        return {
            "is_logged_in": is_logged_in,
            "is_admin": is_admin,
            "user_name": user_name,
            "admin_pending_report_count": admin_pending_report_count,
            "admin_pending_role_count": admin_pending_role_count,
            "active_member": active_member
        }

    # -----------------------------
    # 블루프린트 등록
    # -----------------------------
    from app.api.auth_routes import auth_bp
    from app.api.main_routes import main_bp
    from app.api.report_route import report_bp
    from app.api.admin_routes import admin_bp
    from app.api.admin_report_routes import admin_report_bp
    from app.api.admin_user_routes import admin_user_bp
    from app.api.admin_ai_routes import admin_ai_bp
    from app.api.report_list_routes import report_list_bp
    from app.api.admin_realtime_alert_routes import admin_realtime_alert_bp
    from app.api.realtime_monitor_routes import realtime_monitor_bp
    from app.api.kakao_navigation_routes import kakao_navigation_bp
    from app.api.admin_region_analysis_routes import admin_region_analysis_bp
    from app.api.board_route import board_bp
    from app.api.cctv_routes import cctv_bp


    from app.models import BoardPost, BoardComment

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_report_bp)
    app.register_blueprint(admin_user_bp)
    app.register_blueprint(admin_ai_bp)
    app.register_blueprint(report_list_bp)
    app.register_blueprint(admin_realtime_alert_bp)
    app.register_blueprint(realtime_monitor_bp)
    app.register_blueprint(kakao_navigation_bp)
    app.register_blueprint(admin_region_analysis_bp)
    app.register_blueprint(board_bp)
    app.register_blueprint(cctv_bp)



    # -----------------------------
    # 소켓 이벤트 등록
    # - import만 해도 이벤트 핸들러가 등록되도록 구성
    # -----------------------------
    from app.socket_events import admin_realtime_alert_socket  # noqa: F401

    return app