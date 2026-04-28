import os
import sys

# api_server/app 폴더를 path에 추가
sys.path.append(os.path.abspath("api_server"))

try:
    from app import create_app
    print("create_app import success")
    app = create_app()
    print("App creation success")
except ModuleNotFoundError as e:
    print(f"ModuleNotFoundError detected: {e}")
    # 트레이스백을 통해 정확한 위치 파악
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"Other error: {e}")
    import traceback
    traceback.print_exc()
