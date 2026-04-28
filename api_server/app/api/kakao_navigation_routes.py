# 카카오 네비용 라우트 파일
import os
import requests
from flask import Blueprint, jsonify, request


kakao_navigation_bp = Blueprint(
    "kakao_navigation",
    __name__,
    url_prefix="/api/navigation"
)

KAKAO_MOBILITY_BASE_URL = "https://apis-navi.kakaomobility.com/v1/directions"


def _to_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@kakao_navigation_bp.route("/kakao-route", methods=["GET"])
def get_kakao_route():
    """
    Google 지도는 그대로 사용하고,
    경로 계산만 카카오모빌리티 길찾기 API를 사용하는 프록시 라우트
    """

    kakao_rest_api_key = os.getenv("KAKAO_REST_API_KEY", "").strip()

    if not kakao_rest_api_key:
        return jsonify({
            "success": False,
            "message": "KAKAO_REST_API_KEY가 설정되지 않았습니다."
        }), 500

    origin_lat = _to_float(request.args.get("origin_lat"))
    origin_lng = _to_float(request.args.get("origin_lng"))
    dest_lat = _to_float(request.args.get("dest_lat"))
    dest_lng = _to_float(request.args.get("dest_lng"))

    if None in (origin_lat, origin_lng, dest_lat, dest_lng):
        return jsonify({
            "success": False,
            "message": "출발지/도착지 좌표가 올바르지 않습니다."
        }), 400

    # 동일 좌표 방지
    if abs(origin_lat - dest_lat) < 0.00001 and abs(origin_lng - dest_lng) < 0.00001:
        return jsonify({
            "success": False,
            "message": "출발지와 도착지가 동일합니다."
        }), 400

    params = {
        # 카카오는 origin / destination을 "경도,위도" 순서로 받음
        "origin": f"{origin_lng},{origin_lat}",
        "destination": f"{dest_lng},{dest_lat}",
        "priority": "RECOMMEND",
        "summary": "false",
        "alternatives": "false",
        "road_details": "false"
    }

    headers = {
        "Authorization": f"KakaoAK {kakao_rest_api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(
            KAKAO_MOBILITY_BASE_URL,
            headers=headers,
            params=params,
            timeout=10
        )
    except requests.RequestException as e:
        return jsonify({
            "success": False,
            "message": f"카카오 길찾기 API 요청 중 네트워크 오류가 발생했습니다: {str(e)}"
        }), 502

    if response.status_code != 200:
        return jsonify({
            "success": False,
            "message": "카카오 길찾기 API 호출에 실패했습니다.",
            "status_code": response.status_code,
            "raw": response.text
        }), 502

    data = response.json()
    routes = data.get("routes") or []

    if not routes:
        return jsonify({
            "success": False,
            "message": "카카오 길찾기 결과가 없습니다.",
            "raw": data
        }), 404

    route = routes[0]
    sections = route.get("sections") or []

    # sections -> roads -> vertexes
    # vertexes 형태: [lng1, lat1, lng2, lat2, ...]
    path = []

    for section in sections:
        roads = section.get("roads") or []
        for road in roads:
            vertexes = road.get("vertexes") or []
            for i in range(0, len(vertexes), 2):
                lng = vertexes[i]
                lat = vertexes[i + 1]
                path.append({
                    "lat": lat,
                    "lng": lng
                })

    summary = route.get("summary") or {}

    return jsonify({
        "success": True,
        "data": {
            "distance_m": summary.get("distance", 0),
            "duration_s": summary.get("duration", 0),
            "fare": summary.get("fare", {}),
            "origin": summary.get("origin", {}),
            "destination": summary.get("destination", {}),
            "path": path
        }
    }), 200
