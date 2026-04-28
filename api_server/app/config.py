import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# 환경 변수 로드 (로컬 .env 및 루트 .env)
load_dotenv()
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env")), override=False)


class Config:
    """
    Flask 전체 설정을 관리하는 클래스
    """

    # Flask 세션 암호화 키
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY가 .env에 설정되지 않았습니다.")

    # 데이터베이스 연결 정보
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "ai_accident_detection")

    # 비밀번호에 특수문자가 들어가도 안전하게 처리
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

    # 구글 지도 API 키
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

    ITS_API_KEY = os.getenv("ITS_API_KEY")