"""
Flask 서버 실행 파일
"""

# Flask 앱 생성
from app import create_app
from app.extensions import db, socketio     # extensions에 추가한 소켓 객체
from sqlalchemy import text                 # DB연결 테스트 확인용


app = create_app()

with app.app_context():
    try:
        db.session.execute(text("SELECT 1"))
        print("DB Connection Success")
    except Exception as e:
        print("DB Connection Fail:", e)

    from app.services.its_service import get_its_cctv

    print(get_its_cctv())

    


# 실시간 알림을 위한 소켓 연동으로 변경
if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5001,
        debug=True, # 개발용이라 허용
        allow_unsafe_werkzeug=True # 개발용이라 허용
    )