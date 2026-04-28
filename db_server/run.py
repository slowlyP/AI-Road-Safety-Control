import os
import pymysql
import time
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env")), override=False)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "ai_accident_detection")

def check_db_connection():
    """
    데이터베이스 연결 상태를 점검합니다.
    """
    print(f"--- DB Server Health Check ---")
    print(f"Target Host: {DB_HOST}:{DB_PORT}")
    print(f"Target DB: {DB_NAME}")
    
    try:
        # DB 연결 시도
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=5
        )
        
        with connection.cursor() as cursor:
            # 단순 쿼리 실행 테스트
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result:
                print("Status: SUCCESS")
                print("Connection established successfully.")
                
                # 테이블 목록 확인 (옵션)
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                print(f"Total Tables: {len(tables)}")
            else:
                print("Status: FAILED (No result from query)")
                
        connection.close()
        return True

    except pymysql.err.OperationalError as e:
        print(f"Status: FAILED (Operational Error)")
        print(f"Error Details: {e}")
        if e.args[0] == 2003:
            print("Tip: DB 서버가 켜져 있는지, 네트워크(IP/Port)가 올바른지 확인하세요.")
        elif e.args[0] == 1045:
            print("Tip: DB 사용자(User) 또는 비밀번호(Password)가 틀렸습니다.")
        elif e.args[0] == 1049:
            print(f"Tip: '{DB_NAME}' 데이터베이스가 존재하지 않습니다.")
        return False
        
    except Exception as e:
        print(f"Status: ERROR (Unexpected Exception)")
        print(f"Error Details: {e}")
        return False

if __name__ == "__main__":
    success = check_db_connection()
    
    if success:
        print("\n[DB Server] All systems normal. Ready for service.")
        # 마이크로서비스 구조에서 DB 서버는 실제 프로세스가 떠 있는 것이 아니라 
        # 연결 상태를 유지/관리하는 개념이므로, 체크 후 대기하거나 종료합니다.
        # 여기서는 관리용으로 계속 띄워두고 싶다면 루프를 돌릴 수 있습니다.
        try:
            while True:
                time.sleep(60)
                # 1분마다 생존 신고
                # print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] DB Server is alive...")
        except KeyboardInterrupt:
            print("\nDB Server health check monitor stopped.")
    else:
        print("\n[DB Server] Critical Error: System check failed.")
        exit(1)
