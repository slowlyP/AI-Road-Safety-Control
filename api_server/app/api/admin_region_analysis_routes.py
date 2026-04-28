from flask import Blueprint, jsonify, render_template, request, current_app

from app.common.decorators import login_required, admin_required
from app.services.admin_region_analysis_service import AdminRegionAnalysisService


admin_region_analysis_bp = Blueprint(
    "admin_region_analysis",
    __name__,
    url_prefix="/admin/region-analysis"
)


def _get_days_param(default=30):
    return request.args.get("days", default=default, type=int)


def _get_label_param(default="all"):
    return request.args.get("label", default=default, type=str)


def _get_risk_param(default="all"):
    return request.args.get("risk_level", default=default, type=str)


@admin_region_analysis_bp.route("", methods=["GET"])
@login_required
@admin_required
def region_analysis_page():
    days = _get_days_param(default=30)
    label = _get_label_param(default="all")
    risk_level = _get_risk_param(default="all")

    google_maps_api_key = current_app.config.get("GOOGLE_MAPS_API_KEY", "")

    dashboard_data = AdminRegionAnalysisService.get_dashboard_data(
        days=days,
        detected_label=label,
        risk_level=risk_level,
        limit=10
    )

    return render_template(
        "admin/region_analysis/dashboard.html",
        google_maps_api_key=google_maps_api_key,
        dashboard_data=dashboard_data
    )


@admin_region_analysis_bp.route("/data", methods=["GET"])
@login_required
@admin_required
def get_region_analysis_data():
    days = _get_days_param(default=30)
    label = _get_label_param(default="all")
    risk_level = _get_risk_param(default="all")

    dashboard_data = AdminRegionAnalysisService.get_dashboard_data(
        days=days,
        detected_label=label,
        risk_level=risk_level,
        limit=10
    )

    return jsonify({
        "success": True,
        "data": dashboard_data
    }), 200


@admin_region_analysis_bp.route("/rock-route-analysis", methods=["POST"])
@login_required
@admin_required
def get_rock_route_analysis():
    payload = request.get_json(silent=True) or {}

    path = payload.get("path") or []
    days = payload.get("days", 30)
    radius_km = payload.get("radius_km", 2)

    if not isinstance(path, list) or len(path) < 2:
        return jsonify({
            "success": False,
            "message": "유효한 경로 좌표가 필요합니다."
        }), 400

    try:
        data = AdminRegionAnalysisService.get_rock_route_analysis(
            path=path,
            days=days,
            radius_km=radius_km
        )
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"낙석 경로 분석 중 오류가 발생했습니다: {str(e)}"
        }), 500

    return jsonify({
        "success": True,
        "data": data
    }), 200