from flask import Blueprint, jsonify, render_template, current_app, request, Response

from app.services.realtime_monitor_service import RealtimeMonitorService
from app.services.its_service import get_its_cctv




realtime_monitor_bp = Blueprint(
    "realtime_monitor",
    __name__,
    url_prefix="/realtime-monitor"
)



@realtime_monitor_bp.route("/cctv")
def cctv_dashboard():
    its_data = get_its_cctv()

    # API 응답 구조: its_data['body']['items'] 에 리스트가 들어있음
    # 안전하게 가져오기 위해 .get()을 사용합니다.
    camera_list = its_data.get('body', {}).get('items', [])

    print(f"전달할 카메라 개수: {len(camera_list)}") # 데이터가 잘 담겼는지 확인용

    return render_template(
        "main/cctv_dashboard.html",
        cameras=camera_list  # [수정] 빈 리스트 대신 camera_list를 전달!
    )



def _get_days_param(default=180):
    return request.args.get("days", default=default, type=int)


def _get_limit_param(default):
    return request.args.get("limit", default=default, type=int)


@realtime_monitor_bp.route("", methods=["GET"])
def realtime_monitor_page():
    google_maps_api_key = current_app.config.get("GOOGLE_MAPS_API_KEY", "")
    days = _get_days_param(default=180)

    summary = RealtimeMonitorService.get_summary_cards(days=days)
    risk_list = RealtimeMonitorService.get_recent_risk_list(limit=20, days=days)

    return render_template(
        "main/realtime_monitor.html",
        google_maps_api_key=google_maps_api_key,
        summary=summary,
        risk_list=risk_list,
        default_days=days
    )


@realtime_monitor_bp.route("/summary", methods=["GET"])
def get_summary():
    days = _get_days_param(default=180)
    data = RealtimeMonitorService.get_summary_cards(days=days)

    return jsonify({
        "success": True,
        "data": data,
        "days": days
    }), 200


@realtime_monitor_bp.route("/map-points", methods=["GET"])
def get_map_points():
    days = _get_days_param(default=180)
    limit = _get_limit_param(default=300)

    items = RealtimeMonitorService.get_map_points(limit=20, days=days)

    return jsonify({
        "success": True,
        "items": items,
        "days": days,
        "limit": limit
    }), 200


@realtime_monitor_bp.route("/risk-list", methods=["GET"])
def get_risk_list():
    days = _get_days_param(default=180)
    limit = _get_limit_param(default=20)

    items = RealtimeMonitorService.get_recent_risk_list(limit=20, days=days)

    return jsonify({
        "success": True,
        "items": items,
        "days": days,
        "limit": limit
    }), 200


@realtime_monitor_bp.route("/detail/<int:report_id>", methods=["GET"])
def get_report_detail(report_id):
    detail = RealtimeMonitorService.get_report_detail(report_id)

    if not detail:
        return jsonify({
            "success": False,
            "message": "해당 사고 상세 정보를 찾을 수 없습니다."
        }), 404

    return jsonify({
        "success": True,
        "data": detail
    }), 200
