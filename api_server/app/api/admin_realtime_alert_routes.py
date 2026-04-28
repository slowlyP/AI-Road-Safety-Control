from flask import Blueprint, jsonify, render_template

from app.common.decorators import login_required, admin_required
from app.services.realtime_alert_service import RealtimeAlertService


admin_realtime_alert_bp = Blueprint(
    "admin_realtime_alert",
    __name__,
    url_prefix="/admin/realtime-alerts"
)


@admin_realtime_alert_bp.route("", methods=["GET"])
@login_required
@admin_required
def realtime_alert_page():
    """
    관리자 - 실시간 위험 알림 페이지
    """
    pending_alerts = RealtimeAlertService.get_pending_realtime_alerts(limit=50)
    checked_alerts = RealtimeAlertService.get_checked_realtime_alerts(limit=50)
    pending_count = RealtimeAlertService.get_pending_count()

    return render_template(
        "admin/realtime_alert/list.html",
        unread_alerts=pending_alerts,
        read_alerts=checked_alerts,
        unread_count=pending_count
    )


@admin_realtime_alert_bp.route("/list", methods=["GET"])
@login_required
@admin_required
def get_realtime_alerts():
    """
    실시간 알림 목록 조회
    - 프론트 초기 데이터 확인용
    """
    pending_alerts = RealtimeAlertService.get_pending_realtime_alerts(limit=50)
    checked_alerts = RealtimeAlertService.get_checked_realtime_alerts(limit=50)
    pending_count = RealtimeAlertService.get_pending_count()

    return jsonify({
        "success": True,
        "pending_alerts": pending_alerts,
        "checked_alerts": checked_alerts,
        "pending_count": pending_count
    }), 200


@admin_realtime_alert_bp.route("/unread-count", methods=["GET"])
@login_required
@admin_required
def get_pending_count():
    """
    확인 대기 알림 개수 조회
    - 사이드바 badge 갱신용
    """
    pending_count = RealtimeAlertService.get_pending_count()

    return jsonify({
        "success": True,
        "unread_count": pending_count
    }), 200


@admin_realtime_alert_bp.route("/<int:alert_id>/read", methods=["PATCH", "POST"])
@login_required
@admin_required
def mark_alert_as_checked(alert_id):
    """
    특정 알림 확인 완료 처리
    """
    alert = RealtimeAlertService.mark_as_checked(alert_id)

    if not alert:
        return jsonify({
            "success": False,
            "message": "알림을 찾을 수 없습니다."
        }), 404

    pending_count = RealtimeAlertService.get_pending_count()

    return jsonify({
        "success": True,
        "message": "확인 완료 처리되었습니다.",
        "alert_id": alert_id,
        "unread_count": pending_count
    }), 200


@admin_realtime_alert_bp.route("/read-all", methods=["PATCH", "POST"])
@login_required
@admin_required
def mark_all_alerts_as_checked():
    """
    전체 알림 확인 완료 처리
    """
    updated_count = RealtimeAlertService.mark_all_as_checked()
    pending_count = RealtimeAlertService.get_pending_count()

    return jsonify({
        "success": True,
        "message": f"{updated_count}건 확인 완료 처리되었습니다.",
        "updated_count": updated_count,
        "unread_count": pending_count
    }), 200