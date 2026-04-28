import os
import subprocess
import sys
import time

def run_frontend():
    """
    Vite 기반 프론트엔드 서버를 실행합니다.
    (npm run dev 래퍼)
    """
    print("--- Front Server (Vite) Starter ---")
    
    # node_modules 존재 확인
    if not os.path.exists("node_modules"):
        print("Error: 'node_modules' folder not found.")
        print("Please run 'npm install' first in the 'front_server' directory.")
        return False

    try:
        print("Starting Vite development server on port 3000...")
        # npm run dev 실행 (shell=True는 Windows에서 필요)
        # 3000 포트는 vite.config.js에서 설정됨
        process = subprocess.Popen(["npm", "run", "dev"], shell=True)
        
        print("Front server is booting up. Check http://localhost:3000")
        
        # 프로세스 대기
        process.wait()
        return True

    except KeyboardInterrupt:
        print("\nFront server stopping...")
        return True
    except Exception as e:
        print(f"Failed to start front server: {e}")
        return False

if __name__ == "__main__":
    success = run_frontend()
    if not success:
        sys.exit(1)
