from flask import session, request
from flask_socketio import join_room, leave_room

from app.extensions import socketio


NAMESPACE = "/admin/realtime-alert"
ADMIN_ROOM = "admin_room"


@socketio.on("connect", namespace=NAMESPACE)
def handle_admin_realtime_connect():
    """
    관리자 실시간 위험 알림 소켓 연결

    동작
    1. 세션 기반 관리자 여부 확인
    2. 관리자면 admin_room 입장
    3. 아니면 연결 거부
    """
    user_id = session.get("user_id")
    role = session.get("role")

    print(
        f"[Socket] connect - namespace: {NAMESPACE}, "
        f"user_id: {user_id}, role: {role}, sid: {request.sid}"
    )

    if not user_id:
        print("[Socket] 연결 거부 - 로그인되지 않은 사용자")
        return False

    if role != "admin":
        print(f"[Socket] 연결 거부 - 관리자 아님 (role={role})")
        return False

    join_room(ADMIN_ROOM)
    print(f"[Socket] 관리자 접속 - {ADMIN_ROOM} 입장 완료")


@socketio.on("disconnect", namespace=NAMESPACE)
def handle_admin_realtime_disconnect():
    """
    관리자 실시간 위험 알림 소켓 종료
    """
    role = session.get("role")

    if role == "admin":
        leave_room(ADMIN_ROOM)
        print(f"[Socket] disconnect - {ADMIN_ROOM} 퇴장")

    print(f"[Socket] disconnect - namespace: {NAMESPACE}, sid: {request.sid}")