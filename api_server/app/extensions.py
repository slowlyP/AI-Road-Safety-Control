"""
Flask 확장 라이브러리들을 관리하는 파일

여기서 DB, Migration 등을 생성하고
app/__init__.py에서 초기화한다.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


from flask_socketio import SocketIO


# SQLAlchemy 객체 생성
# 실제 연결은 init_app()에서 이루어진다.
db = SQLAlchemy()

# DB 마이그레이션 관리
# 테이블 변경 시 자동업데이트 지원
migrate = Migrate()


# 연동해서 불러올 소켓 객체 추가
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading"
)