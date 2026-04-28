import math
from collections import defaultdict

from app.repositories.admin_region_analysis_repository import AdminRegionAnalysisRepository


class AdminRegionAnalysisService:
    """
    관리자 위험 지역 분석 서비스
    """

    LABEL_KOR_MAP = {
        "rock": "낙석",
        "box": "박스",
        "bag": "봉투류",
        "tire": "타이어",
        "debris": "기타 낙하물"
    }

    RISK_SCORE_MAP = {
        "긴급": 3,
        "위험": 2,
        "주의": 1
    }

    @staticmethod
    def _safe_float(value, default=0.0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _sanitize_days(days, default=30):
        try:
            value = int(days)
            if value <= 0:
                return default
            return min(value, 365)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _sanitize_limit(limit, default=10, max_limit=50):
        try:
            value = int(limit)
            if value <= 0:
                return default
            return min(value, max_limit)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _sanitize_radius(radius_km, default=2.0):
        try:
            value = float(radius_km)
            if value <= 0:
                return default
            return min(value, 10.0)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _format_datetime(dt):
        if not dt:
            return "-"
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _extract_district(location_text):
        if not location_text:
            return "지역 미상"

        text = str(location_text).replace(",", " ").strip()
        tokens = [token for token in text.split() if token]

        if not tokens:
            return "지역 미상"

        for token in tokens:
            if token.endswith("구"):
                return token

        for token in tokens:
            if token.endswith("군") or token.endswith("시"):
                return token

        return tokens[0]

    @staticmethod
    def _score_to_risk_label(score):
        if score >= 3:
            return "긴급"
        if score == 2:
            return "위험"
        if score == 1:
            return "주의"
        return "-"

    @staticmethod
    def _build_point_items(rows):
        point_items = []
        seen_report_ids = set()

        for row in rows:
            if row.report_id in seen_report_ids:
                continue
            seen_report_ids.add(row.report_id)

            point_items.append({
                "report_id": row.report_id,
                "title": row.title or "제목 없음",
                "location_text": row.location_text or "위치 정보 없음",
                "district_name": AdminRegionAnalysisService._extract_district(row.location_text),
                "latitude": AdminRegionAnalysisService._safe_float(row.latitude),
                "longitude": AdminRegionAnalysisService._safe_float(row.longitude),
                "risk_level": row.risk_level or "주의",
                "status": row.status or "-",
                "detected_label": row.detected_label or "unknown",
                "detected_label_kor": AdminRegionAnalysisService.LABEL_KOR_MAP.get(
                    row.detected_label,
                    row.detected_label or "미확인"
                ),
                "confidence": round(AdminRegionAnalysisService._safe_float(row.confidence), 2),
                "created_at": AdminRegionAnalysisService._format_datetime(row.created_at),
            })

        return point_items

    @staticmethod
    def _build_district_summary(points, limit=4):
        district_map = defaultdict(lambda: {
            "district_name": "",
            "incident_count": 0,
            "emergency_count": 0,
            "rock_count": 0,
            "max_risk_score": 0
        })

        for item in points:
            district_name = item.get("district_name") or "지역 미상"
            risk_level = item.get("risk_level")
            detected_label = item.get("detected_label")

            district_map[district_name]["district_name"] = district_name
            district_map[district_name]["incident_count"] += 1
            district_map[district_name]["max_risk_score"] = max(
                district_map[district_name]["max_risk_score"],
                AdminRegionAnalysisService.RISK_SCORE_MAP.get(risk_level, 0)
            )

            if risk_level == "긴급":
                district_map[district_name]["emergency_count"] += 1

            if detected_label == "rock":
                district_map[district_name]["rock_count"] += 1

        district_items = list(district_map.values())
        district_items.sort(
            key=lambda item: (
                item["incident_count"],
                item["max_risk_score"],
                item["rock_count"]
            ),
            reverse=True
        )

        result = []
        for item in district_items[:limit]:
            result.append({
                "district_name": item["district_name"],
                "incident_count": item["incident_count"],
                "emergency_count": item["emergency_count"],
                "rock_count": item["rock_count"],
                "max_risk_level": AdminRegionAnalysisService._score_to_risk_label(item["max_risk_score"])
            })

        return result

    @staticmethod
    def _build_rock_focus_summary(points, rock_points):
        total_incidents = len(points)
        rock_incidents = len(rock_points)
        rock_ratio = round((rock_incidents / total_incidents) * 100, 1) if total_incidents > 0 else 0.0

        emergency_rock_count = sum(1 for item in rock_points if item.get("risk_level") == "긴급")

        district_map = defaultdict(int)
        for item in rock_points:
            district_name = item.get("district_name") or "지역 미상"
            district_map[district_name] += 1

        top_rock_district = "-"
        top_rock_district_count = 0

        if district_map:
            top_rock_district, top_rock_district_count = max(
                district_map.items(),
                key=lambda x: x[1]
            )

        if rock_incidents == 0:
            message = "현재 조건에서는 낙석 사고가 확인되지 않았습니다."
        elif emergency_rock_count >= 1:
            message = "긴급 낙석 사고가 포함되어 있어 우선 관리가 필요한 구간이 존재합니다."
        elif rock_ratio >= 40:
            message = "전체 사고 중 낙석 비중이 높아 공사 차량·중장비 운행 시 주의가 필요합니다."
        else:
            message = "낙석 사고는 존재하지만 전체 비중은 상대적으로 안정적인 수준입니다."

        return {
            "rock_incidents": rock_incidents,
            "rock_ratio": rock_ratio,
            "emergency_rock_count": emergency_rock_count,
            "top_rock_district": top_rock_district,
            "top_rock_district_count": top_rock_district_count,
            "message": message
        }

    @staticmethod
    def _distance_point_to_segment_km(point, start, end):
        lat_scale = 111
        lng_scale = 111 * math.cos(math.radians((start["lat"] + end["lat"]) / 2))

        px = point["lng"] * lng_scale
        py = point["lat"] * lat_scale
        x1 = start["lng"] * lng_scale
        y1 = start["lat"] * lat_scale
        x2 = end["lng"] * lng_scale
        y2 = end["lat"] * lat_scale

        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)

        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy

        return math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)

    @staticmethod
    def _is_point_near_path(lat, lng, path, radius_km=2.0):
        if not path or len(path) < 2:
            return False

        point = {"lat": float(lat), "lng": float(lng)}
        min_distance = float("inf")

        for i in range(len(path) - 1):
            start = path[i]
            end = path[i + 1]
            distance = AdminRegionAnalysisService._distance_point_to_segment_km(point, start, end)
            min_distance = min(min_distance, distance)

        return min_distance <= radius_km

    @staticmethod
    def get_dashboard_data(days=30, detected_label="all", risk_level="all", limit=10):
        days = AdminRegionAnalysisService._sanitize_days(days)
        limit = AdminRegionAnalysisService._sanitize_limit(limit)

        summary = AdminRegionAnalysisRepository.get_summary_data(
            days=days,
            detected_label=detected_label,
            risk_level=risk_level
        )

        filtered_rows = AdminRegionAnalysisRepository.get_region_points(
            days=days,
            detected_label=detected_label,
            risk_level=risk_level
        )

        rock_rows = AdminRegionAnalysisRepository.get_region_points(
            days=days,
            detected_label="rock",
            risk_level=risk_level
        )

        label_distribution = AdminRegionAnalysisRepository.get_label_distribution(
            days=days,
            risk_level=risk_level
        )

        risk_distribution = AdminRegionAnalysisRepository.get_risk_distribution(
            days=days,
            detected_label=detected_label
        )

        top_regions = AdminRegionAnalysisRepository.get_top_regions(
            days=days,
            detected_label=detected_label,
            risk_level=risk_level,
            limit=limit
        )

        point_items = AdminRegionAnalysisService._build_point_items(filtered_rows)
        rock_point_items = AdminRegionAnalysisService._build_point_items(rock_rows)

        label_items = []
        for row in label_distribution:
            label_items.append({
                "label": row.label or "unknown",
                "label_kor": AdminRegionAnalysisService.LABEL_KOR_MAP.get(
                    row.label,
                    row.label or "미확인"
                ),
                "count": int(row.count or 0)
            })

        temp_risk_items = []
        for row in risk_distribution:
            temp_risk_items.append({
                "risk_level": row.risk_level or "-",
                "count": int(row.count or 0)
            })

        temp_risk_items.sort(
            key=lambda item: AdminRegionAnalysisService.RISK_SCORE_MAP.get(item["risk_level"], 0),
            reverse=True
        )
        risk_items = temp_risk_items

        top_region_items = []
        for row in top_regions:
            score = int(row.max_risk_score or 0)
            top_region_items.append({
                "location_text": row.location_text or "위치 정보 없음",
                "incident_count": int(row.incident_count or 0),
                "max_risk_level": AdminRegionAnalysisService._score_to_risk_label(score)
            })

        district_summary = AdminRegionAnalysisService._build_district_summary(
            point_items,
            limit=4
        )

        rock_focus_summary = AdminRegionAnalysisService._build_rock_focus_summary(
            point_items,
            rock_point_items
        )

        return {
            "summary": summary,
            "points": point_items,
            "label_distribution": label_items,
            "risk_distribution": risk_items,
            "top_regions": top_region_items,
            "district_summary": district_summary,
            "rock_focus_summary": rock_focus_summary,
            "filters": {
                "days": days,
                "detected_label": detected_label,
                "risk_level": risk_level
            }
        }

    @staticmethod
    def get_rock_route_analysis(path, days=30, radius_km=2.0):
        days = AdminRegionAnalysisService._sanitize_days(days)
        radius_km = AdminRegionAnalysisService._sanitize_radius(radius_km)

        rows = AdminRegionAnalysisRepository.get_rock_points_by_days(days=days)
        point_items = AdminRegionAnalysisService._build_point_items(rows)

        filtered_items = []
        for item in point_items:
            if AdminRegionAnalysisService._is_point_near_path(
                lat=item["latitude"],
                lng=item["longitude"],
                path=path,
                radius_km=radius_km
            ):
                filtered_items.append(item)

        emergency_count = sum(1 for item in filtered_items if item["risk_level"] == "긴급")

        district_map = defaultdict(int)
        for item in filtered_items:
            district_map[item["district_name"]] += 1

        top_district = "-"
        top_district_count = 0
        if district_map:
            top_district, top_district_count = max(district_map.items(), key=lambda x: x[1])

        if not filtered_items:
            message = "선택한 경로 2km 반경 내 최근 낙석 사고가 확인되지 않았습니다."
        elif emergency_count >= 1:
            message = "선택한 경로 주변에 긴급 낙석 사고 이력이 있어 우회 검토가 필요합니다."
        elif len(filtered_items) >= 5:
            message = "선택한 경로 주변에 낙석 사고가 반복적으로 발생했습니다. 주의 운행이 필요합니다."
        else:
            message = "선택한 경로 주변에 일부 낙석 사고 이력이 있습니다. 주의가 필요합니다."

        return {
            "summary": {
                "rock_count": len(filtered_items),
                "emergency_rock_count": emergency_count,
                "top_district": top_district,
                "top_district_count": top_district_count,
                "risk_message": message,
            },
            "items": filtered_items
        }