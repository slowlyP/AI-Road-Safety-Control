let realtimeMonitorMap = null;
let realtimeMonitorInfoWindow = null;
let realtimeMonitorMarkers = [];
let realtimeRoutePolyline = null;

let ALL_MAP_POINTS = [];
let ALL_RISK_LIST = [];

let CURRENT_RISK_FILTER = "all";
let CURRENT_USER_POSITION = null;
let CURRENT_RADIUS_KM = 3;
let CURRENT_SORT_TYPE = "risk_desc";

let CURRENT_ROUTE_ACTIVE = false;
let CURRENT_ROUTE_POINTS = [];
let CURRENT_ROUTE_RADIUS_KM = 0.5;

let CURRENT_VISIBLE_DAYS = 180;
let HAS_INITIAL_MAP_FIT = false;

let INFO_WINDOW_CLOSE_TIMER = null;

// 자동완성 관련 상태
let ORIGIN_AUTOCOMPLETE = null;
let DESTINATION_AUTOCOMPLETE = null;
let SELECTED_ORIGIN_PLACE = null;
let SELECTED_DESTINATION_PLACE = null;
let ROUTE_AUTOCOMPLETE_AVAILABLE = false;
let ROUTE_AUTOCOMPLETE_NOTICE_SHOWN = false;

function showLoading(text = "데이터 불러오는 중...") {
    const overlay = document.getElementById("global-loading-overlay");
    const textEl = document.getElementById("loading-text");

    if (textEl) {
        textEl.textContent = text;
    }

    if (overlay) {
        overlay.classList.remove("hidden");
    }
}

function hideLoading() {
    const overlay = document.getElementById("global-loading-overlay");
    if (overlay) {
        overlay.classList.add("hidden");
    }
}

async function fetchJson(url) {
    const response = await fetch(url, {
        method: "GET",
        headers: {
            "X-Requested-With": "XMLHttpRequest"
        }
    });

    let json = null;
    try {
        json = await response.json();
    } catch (e) {
        json = null;
    }

    if (!response.ok) {
        const message = json?.message || `HTTP ${response.status}`;
        throw new Error(message);
    }

    return json;
}

function buildApiUrl(baseUrl, params = {}) {
    const url = new URL(baseUrl, window.location.origin);

    Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
            url.searchParams.set(key, value);
        }
    });

    return url.toString();
}

function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value ?? "";
    return div.innerHTML;
}

function getMarkerIconByRiskLevel(riskLevel) {
    switch (riskLevel) {
        case "긴급":
            return "http://maps.google.com/mapfiles/ms/icons/red-dot.png";
        case "위험":
            return "http://maps.google.com/mapfiles/ms/icons/orange-dot.png";
        case "주의":
        default:
            return "http://maps.google.com/mapfiles/ms/icons/yellow-dot.png";
    }
}

function getRiskPriority(riskLevel) {
    switch (riskLevel) {
        case "긴급":
            return 3;
        case "위험":
            return 2;
        case "주의":
            return 1;
        default:
            return 0;
    }
}

function parseConfidence(value) {
    const num = Number(value);
    return Number.isNaN(num) ? 0 : num;
}

function parseDateValue(value) {
    if (!value) return 0;
    const time = new Date(value).getTime();
    return Number.isNaN(time) ? 0 : time;
}

function sortRiskItems(items) {
    const copied = [...items];

    copied.sort((a, b) => {
        if (CURRENT_SORT_TYPE === "confidence_desc") {
            const diff = parseConfidence(b.confidence) - parseConfidence(a.confidence);
            if (diff !== 0) return diff;

            const riskDiff = getRiskPriority(b.risk_level) - getRiskPriority(a.risk_level);
            if (riskDiff !== 0) return riskDiff;

            return parseDateValue(b.created_at) - parseDateValue(a.created_at);
        }

        if (CURRENT_SORT_TYPE === "latest") {
            const diff = parseDateValue(b.created_at) - parseDateValue(a.created_at);
            if (diff !== 0) return diff;

            const riskDiff = getRiskPriority(b.risk_level) - getRiskPriority(a.risk_level);
            if (riskDiff !== 0) return riskDiff;

            return parseConfidence(b.confidence) - parseConfidence(a.confidence);
        }

        const riskDiff = getRiskPriority(b.risk_level) - getRiskPriority(a.risk_level);
        if (riskDiff !== 0) return riskDiff;

        const confidenceDiff = parseConfidence(b.confidence) - parseConfidence(a.confidence);
        if (confidenceDiff !== 0) return confidenceDiff;

        return parseDateValue(b.created_at) - parseDateValue(a.created_at);
    });

    return copied;
}

function clearMarkers() {
    realtimeMonitorMarkers.forEach((marker) => marker.setMap(null));
    realtimeMonitorMarkers = [];
}

function hideRouteSummary() {
    const panel = document.getElementById("route-risk-summary-panel");
    if (panel) {
        panel.classList.add("hidden");
    }
}

function showRouteSummary() {
    const panel = document.getElementById("route-risk-summary-panel");
    if (panel) {
        panel.classList.remove("hidden");
    }
}

function setRouteSummaryBadge(levelText, className) {
    const badge = document.getElementById("route-risk-overall-badge");
    if (!badge) return;

    badge.className = "route-risk-overall-badge";
    if (className) {
        badge.classList.add(className);
    }
    badge.textContent = levelText;
}

function updateRouteRiskSummary(items) {
    const totalEl = document.getElementById("route-summary-total-count");
    const emergencyEl = document.getElementById("route-summary-emergency-count");
    const dangerEl = document.getElementById("route-summary-danger-count");
    const warningEl = document.getElementById("route-summary-warning-count");
    const messageEl = document.getElementById("route-summary-message");

    if (!CURRENT_ROUTE_ACTIVE) {
        hideRouteSummary();
        return;
    }

    const counts = {
        emergency: 0,
        danger: 0,
        warning: 0
    };

    items.forEach((item) => {
        if (item.risk_level === "긴급") {
            counts.emergency += 1;
        } else if (item.risk_level === "위험") {
            counts.danger += 1;
        } else {
            counts.warning += 1;
        }
    });

    const totalCount = items.length;

    if (totalEl) totalEl.textContent = totalCount;
    if (emergencyEl) emergencyEl.textContent = counts.emergency;
    if (dangerEl) dangerEl.textContent = counts.danger;
    if (warningEl) warningEl.textContent = counts.warning;

    if (totalCount === 0) {
        setRouteSummaryBadge("안전", "safe");
        if (messageEl) {
            messageEl.textContent = "현재 선택한 경로 반경 내에서 위험 지점이 확인되지 않았습니다.";
        }
    } else if (counts.emergency >= 1) {
        setRouteSummaryBadge("매우 높음", "critical");
        if (messageEl) {
            messageEl.textContent = "긴급 위험이 포함된 경로입니다. 가능하면 우회하거나 각별한 주의 운전이 필요합니다.";
        }
    } else if (counts.danger >= 2 || totalCount >= 5) {
        setRouteSummaryBadge("높음", "danger");
        if (messageEl) {
            messageEl.textContent = "위험 지점이 다수 포함된 경로입니다. 감속 운전 및 전방 주시를 권장합니다.";
        }
    } else if (counts.danger >= 1 || counts.warning >= 2) {
        setRouteSummaryBadge("보통", "warning");
        if (messageEl) {
            messageEl.textContent = "일부 주의 구간이 포함되어 있습니다. 주변 상황을 확인하며 이동해주세요.";
        }
    } else {
        setRouteSummaryBadge("낮음", "normal");
        if (messageEl) {
            messageEl.textContent = "상대적으로 안정적인 경로지만 기본적인 안전 운전은 계속 유지해주세요.";
        }
    }

    showRouteSummary();
}

function clearRoute() {
    CURRENT_ROUTE_ACTIVE = false;
    CURRENT_ROUTE_POINTS = [];
    CURRENT_ROUTE_RADIUS_KM = 0.5;
    SELECTED_ORIGIN_PLACE = null;
    SELECTED_DESTINATION_PLACE = null;

    const originInput = document.getElementById("route-origin");
    const destinationInput = document.getElementById("route-destination");
    if (originInput) originInput.value = "";
    if (destinationInput) destinationInput.value = "";

    if (realtimeRoutePolyline) {
        realtimeRoutePolyline.setMap(null);
        realtimeRoutePolyline = null;
    }

    const title = document.getElementById("risk-list-title");
    const subtitle = document.getElementById("risk-list-subtitle");

    if (title) title.textContent = "실시간 위험 리스트";
    if (subtitle) subtitle.textContent = "최근 탐지된 위험 이벤트를 빠르게 확인할 수 있습니다.";

    hideRouteSummary();
}

function normalizeFileType(fileType) {
    return String(fileType || "").trim();
}

function buildPreviewMediaHtml(item) {
    const thumbnailPath = item.thumbnail_path || item.file_path || "";
    const fileType = normalizeFileType(item.file_type);

    if (!thumbnailPath) {
        return `
            <div style="
                width: 100%;
                height: 150px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #f3f4f6;
                color: #6b7280;
                font-size: 13px;
                border-radius: 10px;
                margin-bottom: 10px;
            ">
                미리보기 없음
            </div>
        `;
    }

    if (fileType === "이미지") {
        return `
            <img
                src="${escapeHtml(thumbnailPath)}"
                alt="위험 미리보기"
                style="
                    width: 100%;
                    height: 150px;
                    object-fit: cover;
                    border-radius: 10px;
                    display: block;
                    margin-bottom: 10px;
                    background: #f3f4f6;
                "
            >
        `;
    }

    if (fileType === "영상") {
        return `
            <video
                src="${escapeHtml(thumbnailPath)}"
                muted
                playsinline
                preload="metadata"
                style="
                    width: 100%;
                    height: 150px;
                    object-fit: cover;
                    border-radius: 10px;
                    display: block;
                    margin-bottom: 10px;
                    background: #111827;
                "
            ></video>
        `;
    }

    return `
        <div style="
            width: 100%;
            height: 150px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f3f4f6;
            color: #6b7280;
            font-size: 13px;
            border-radius: 10px;
            margin-bottom: 10px;
        ">
            미리보기 없음
        </div>
    `;
}

function buildInfoWindowContent(item) {
    return `
        <div class="map-info-window" style="width: 260px; padding: 4px 2px;">
            ${buildPreviewMediaHtml(item)}

            <div
                class="map-info-title"
                style="
                    font-weight: 700;
                    font-size: 14px;
                    color: #111827;
                    margin-bottom: 8px;
                    line-height: 1.4;
                "
            >
                ${escapeHtml(item.location_text || "위치 정보 없음")}
            </div>

            <div class="map-info-row" style="font-size: 13px; margin-bottom: 4px;">
                <strong>위험도:</strong> ${escapeHtml(item.risk_level || "-")}
            </div>
            <div class="map-info-row" style="font-size: 13px; margin-bottom: 4px;">
                <strong>장애물:</strong> ${escapeHtml(item.detected_label || "-")}
            </div>
            <div class="map-info-row" style="font-size: 13px; margin-bottom: 4px;">
                <strong>접수 시간:</strong> ${escapeHtml(item.created_at || "-")}
            </div>
            <div class="map-info-row" style="font-size: 13px; margin-bottom: 4px;">
                <strong>처리 상태:</strong> ${escapeHtml(item.status || "-")}
            </div>
            <div class="map-info-row" style="font-size: 13px;">
                <strong>신뢰도:</strong> ${escapeHtml(String(item.confidence ?? "-"))}
            </div>
        </div>
    `;
}

function openMarkerPreview(marker, item) {
    if (!realtimeMonitorInfoWindow) {
        realtimeMonitorInfoWindow = new google.maps.InfoWindow();
    }

    if (INFO_WINDOW_CLOSE_TIMER) {
        clearTimeout(INFO_WINDOW_CLOSE_TIMER);
        INFO_WINDOW_CLOSE_TIMER = null;
    }

    realtimeMonitorInfoWindow.setContent(buildInfoWindowContent(item));
    realtimeMonitorInfoWindow.open({
        anchor: marker,
        map: realtimeMonitorMap
    });
}

function closeMarkerPreviewWithDelay(delay = 120) {
    if (INFO_WINDOW_CLOSE_TIMER) {
        clearTimeout(INFO_WINDOW_CLOSE_TIMER);
    }

    INFO_WINDOW_CLOSE_TIMER = setTimeout(() => {
        if (realtimeMonitorInfoWindow) {
            realtimeMonitorInfoWindow.close();
        }
    }, delay);
}

function createRiskListItem(item) {
    const wrapper = document.createElement("div");
    wrapper.className = `risk-list-item risk-${item.risk_level || "주의"}`;
    wrapper.dataset.reportId = item.report_id || "";

    wrapper.innerHTML = `
        <div class="risk-list-top">
            <span class="risk-badge risk-${item.risk_level || "주의"}">${escapeHtml(item.risk_level || "주의")}</span>
            <span class="risk-time">${escapeHtml(item.time_ago || "-")}</span>
        </div>

        <div class="risk-location">${escapeHtml(item.location_text || "위치 정보 없음")}</div>

        <div class="risk-meta">
            <span>장애물: ${escapeHtml(item.detected_label || "-")}</span>
            <span>상태: ${escapeHtml(item.status || "-")}</span>
        </div>

        <div class="risk-extra">
            <span>신고ID: ${escapeHtml(String(item.report_id || "-"))}</span>
            <span>신뢰도: ${escapeHtml(String(item.confidence ?? "-"))}</span>
        </div>
    `;

    wrapper.addEventListener("click", () => {
        if (item.report_id) {
            openRiskDetailModal(item.report_id);
        }
    });

    return wrapper;
}

function haversineDistanceKm(lat1, lng1, lat2, lng2) {
    const toRad = (deg) => deg * (Math.PI / 180);
    const R = 6371;

    const dLat = toRad(lat2 - lat1);
    const dLng = toRad(lng2 - lng1);

    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
        Math.sin(dLng / 2) * Math.sin(dLng / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

function matchesRiskFilter(item) {
    if (CURRENT_RISK_FILTER === "all") {
        return true;
    }
    return item.risk_level === CURRENT_RISK_FILTER;
}

function matchesNearbyFilter(item) {
    if (!CURRENT_USER_POSITION) {
        return true;
    }

    const lat = Number(item.latitude);
    const lng = Number(item.longitude);

    if (!lat || !lng) {
        return false;
    }

    const distance = haversineDistanceKm(
        CURRENT_USER_POSITION.lat,
        CURRENT_USER_POSITION.lng,
        lat,
        lng
    );

    return distance <= CURRENT_RADIUS_KM;
}

function distancePointToSegmentKm(point, start, end) {
    const latScale = 111;
    const lngScale = 111 * Math.cos(((start.lat + end.lat) / 2) * Math.PI / 180);

    const px = point.lng * lngScale;
    const py = point.lat * latScale;
    const x1 = start.lng * lngScale;
    const y1 = start.lat * latScale;
    const x2 = end.lng * lngScale;
    const y2 = end.lat * latScale;

    const dx = x2 - x1;
    const dy = y2 - y1;

    if (dx === 0 && dy === 0) {
        return Math.sqrt((px - x1) ** 2 + (py - y1) ** 2);
    }

    const t = Math.max(0, Math.min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)));
    const projX = x1 + t * dx;
    const projY = y1 + t * dy;

    return Math.sqrt((px - projX) ** 2 + (py - projY) ** 2);
}

function isPointNearRoute(item) {
    if (!CURRENT_ROUTE_ACTIVE || CURRENT_ROUTE_POINTS.length < 2) {
        return true;
    }

    const point = {
        lat: Number(item.latitude),
        lng: Number(item.longitude)
    };

    if (!point.lat || !point.lng) {
        return false;
    }

    let minDistance = Infinity;

    for (let i = 0; i < CURRENT_ROUTE_POINTS.length - 1; i += 1) {
        const start = CURRENT_ROUTE_POINTS[i];
        const end = CURRENT_ROUTE_POINTS[i + 1];
        const distance = distancePointToSegmentKm(point, start, end);

        if (distance < minDistance) {
            minDistance = distance;
        }
    }

    return minDistance <= CURRENT_ROUTE_RADIUS_KM;
}

function getFilteredMapPoints() {
    return ALL_MAP_POINTS.filter((item) => {
        return matchesRiskFilter(item) && matchesNearbyFilter(item) && isPointNearRoute(item);
    });
}

function getFilteredRiskList() {
    const filtered = ALL_RISK_LIST.filter((item) => {
        if (!matchesRiskFilter(item)) {
            return false;
        }

        const matched = ALL_MAP_POINTS.find((p) => p.report_id === item.report_id);
        if (!matched) {
            return !CURRENT_USER_POSITION && !CURRENT_ROUTE_ACTIVE;
        }

        if (!matchesNearbyFilter(matched)) {
            return false;
        }

        if (!isPointNearRoute(matched)) {
            return false;
        }

        return true;
    });

    return sortRiskItems(filtered);
}

function updateFilterStatus() {
    const statusEl = document.getElementById("monitor-filter-status");
    if (!statusEl) return;

    const riskText = CURRENT_RISK_FILTER === "all" ? "전체 위험도" : `${CURRENT_RISK_FILTER}만`;
    const nearbyText = CURRENT_USER_POSITION
        ? `내 주변 반경 ${CURRENT_RADIUS_KM}km 기준으로`
        : "전체 지역 기준으로";

    const routeText = CURRENT_ROUTE_ACTIVE
        ? ` 경로 반경 ${CURRENT_ROUTE_RADIUS_KM}km 조건도 함께 적용 중입니다.`
        : "";

    let sortText = " 위험도 높은 순으로 정렬 중입니다.";
    if (CURRENT_SORT_TYPE === "latest") {
        sortText = " 최신순으로 정렬 중입니다.";
    } else if (CURRENT_SORT_TYPE === "confidence_desc") {
        sortText = " 신뢰도 높은 순으로 정렬 중입니다.";
    }

    statusEl.textContent = `${nearbyText} ${riskText} 표시하고 있습니다.${routeText}${sortText}`;
}

function renderMapPoints(points, options = {}) {
    if (!realtimeMonitorMap) return;

    const preserveView = options.preserveView ?? true;
    const currentCenter = preserveView ? realtimeMonitorMap.getCenter() : null;
    const currentZoom = preserveView ? realtimeMonitorMap.getZoom() : null;

    clearMarkers();

    const bounds = new google.maps.LatLngBounds();
    let validCount = 0;

    points.forEach((item) => {
        const lat = Number(item.latitude);
        const lng = Number(item.longitude);

        if (!lat || !lng) return;

        const marker = new google.maps.Marker({
            position: { lat, lng },
            map: realtimeMonitorMap,
            title: item.location_text || "위치 정보 없음",
            icon: getMarkerIconByRiskLevel(item.risk_level)
        });

        marker.addListener("mouseover", () => {
            openMarkerPreview(marker, item);
        });

        marker.addListener("mouseout", () => {
            closeMarkerPreviewWithDelay(120);
        });

        marker.addListener("click", () => {
            if (item.report_id) {
                openRiskDetailModal(item.report_id);
            }
        });

        realtimeMonitorMarkers.push(marker);
        bounds.extend({ lat, lng });
        validCount += 1;
    });

    if (CURRENT_USER_POSITION) {
        const userMarker = new google.maps.Marker({
            position: CURRENT_USER_POSITION,
            map: realtimeMonitorMap,
            title: "내 현재 위치",
            icon: "http://maps.google.com/mapfiles/ms/icons/blue-dot.png"
        });

        realtimeMonitorMarkers.push(userMarker);
        bounds.extend(CURRENT_USER_POSITION);
        validCount += 1;
    }

    if (validCount === 0) {
        return;
    }

    if (!HAS_INITIAL_MAP_FIT) {
        realtimeMonitorMap.fitBounds(bounds);

        const listener = google.maps.event.addListener(realtimeMonitorMap, "idle", function () {
            if (realtimeMonitorMap.getZoom() > 15) {
                realtimeMonitorMap.setZoom(15);
            }
            google.maps.event.removeListener(listener);
        });

        HAS_INITIAL_MAP_FIT = true;
        return;
    }

    if (preserveView && currentCenter && currentZoom) {
        realtimeMonitorMap.setCenter(currentCenter);
        realtimeMonitorMap.setZoom(currentZoom);
    }
}

function renderRiskList(items) {
    const listContainer = document.getElementById("realtime-risk-list");
    if (!listContainer) return;

    listContainer.innerHTML = "";

    if (items.length === 0) {
        listContainer.innerHTML = `
            <div class="risk-empty-state">
                현재 조건에 맞는 위험 데이터가 없습니다.
            </div>
        `;
        return;
    }

    items.forEach((item) => {
        listContainer.appendChild(createRiskListItem(item));
    });
}

function applyFiltersAndRender(options = {}) {
    const filteredMapPoints = getFilteredMapPoints();
    const filteredRiskList = getFilteredRiskList();

    renderMapPoints(filteredMapPoints, options);
    renderRiskList(filteredRiskList);
    updateFilterStatus();

    if (CURRENT_ROUTE_ACTIVE) {
        updateRouteRiskSummary(filteredRiskList);
    } else {
        hideRouteSummary();
    }
}

async function loadMapPoints() {
    if (!window.REALTIME_MONITOR_CONFIG) return;

    const url = buildApiUrl(window.REALTIME_MONITOR_CONFIG.mapPointsApiUrl, {
        days: CURRENT_VISIBLE_DAYS,
        limit: 300
    });

    const result = await fetchJson(url);
    if (!result.success) return;

    ALL_MAP_POINTS = result.items || [];
}

async function loadSummaryCards() {
    if (!window.REALTIME_MONITOR_CONFIG) return;

    const url = buildApiUrl(window.REALTIME_MONITOR_CONFIG.summaryApiUrl, {
        days: CURRENT_VISIBLE_DAYS
    });

    const result = await fetchJson(url);
    if (!result.success) return;

    const data = result.data || {};

    const currentRiskZones = document.getElementById("summary-current-risk-zones");
    const todayReports = document.getElementById("summary-today-reports");
    const emergencyLast24h = document.getElementById("summary-emergency-last-24h");
    const hotspots = document.getElementById("summary-hotspots");

    if (currentRiskZones) currentRiskZones.textContent = data.current_risk_zones ?? 0;
    if (todayReports) todayReports.textContent = data.today_reports ?? 0;
    if (emergencyLast24h) emergencyLast24h.textContent = data.emergency_last_24h ?? 0;
    if (hotspots) hotspots.textContent = data.hotspots ?? 0;
}

async function loadRiskList() {
    if (!window.REALTIME_MONITOR_CONFIG) return;

    const url = buildApiUrl(window.REALTIME_MONITOR_CONFIG.riskListApiUrl, {
        days: CURRENT_VISIBLE_DAYS,
        limit: 20
    });

    const result = await fetchJson(url);
    if (!result.success) return;

    ALL_RISK_LIST = result.items || [];
}

async function refreshRealtimeMonitorData(options = {}) {
    const preserveView = options.preserveView ?? true;
    const showOverlay = options.showOverlay ?? true;

    try {
        if (showOverlay) {
            showLoading("데이터 불러오는 중...");
        }

        await Promise.all([
            loadSummaryCards(),
            loadMapPoints(),
            loadRiskList()
        ]);

        applyFiltersAndRender({ preserveView });
    } catch (error) {
        console.error("탐지 현황 데이터 갱신 실패:", error);
    } finally {
        if (showOverlay) {
            hideLoading();
        }
    }
}

function bindRiskFilterButtons() {
    const buttons = document.querySelectorAll(".filter-btn[data-risk-filter]");
    buttons.forEach((btn) => {
        btn.addEventListener("click", () => {
            buttons.forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");

            CURRENT_RISK_FILTER = btn.dataset.riskFilter || "all";
            applyFiltersAndRender({ preserveView: true });
        });
    });
}

function bindRadiusSelect() {
    const radiusSelect = document.getElementById("nearby-radius-select");
    if (!radiusSelect) return;

    radiusSelect.addEventListener("change", () => {
        CURRENT_RADIUS_KM = Number(radiusSelect.value || 3);

        if (CURRENT_USER_POSITION) {
            applyFiltersAndRender({ preserveView: true });
        }
    });
}

function bindSortSelect() {
    const sortSelect = document.getElementById("risk-sort-select");
    if (!sortSelect) return;

    sortSelect.addEventListener("change", () => {
        CURRENT_SORT_TYPE = sortSelect.value || "risk_desc";
        applyFiltersAndRender({ preserveView: true });
    });
}

function bindNearbyButtons() {
    const findBtn = document.getElementById("find-nearby-risk-btn");
    const resetBtn = document.getElementById("reset-nearby-risk-btn");

    if (findBtn) {
        findBtn.addEventListener("click", () => {
            alert("현재 위치 기반 기능은 API 권한 연동 후 사용할 수 있습니다. 지금은 전체 보기, 위험도 필터, 경로 위험 보기를 중심으로 확인해주세요.");
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener("click", () => {
            CURRENT_USER_POSITION = null;
            applyFiltersAndRender({ preserveView: true });
        });
    }
}

function initRouteAutocomplete() {
    const originInput = document.getElementById("route-origin");
    const destinationInput = document.getElementById("route-destination");

    if (!originInput || !destinationInput) {
        return;
    }

    if (!google.maps.places || !google.maps.places.Autocomplete) {
        ROUTE_AUTOCOMPLETE_AVAILABLE = false;

        if (!ROUTE_AUTOCOMPLETE_NOTICE_SHOWN) {
            ROUTE_AUTOCOMPLETE_NOTICE_SHOWN = true;
            alert("현재 자동완성 기능을 사용할 수 없습니다. Google Maps Places API 설정을 확인해주세요.");
        }
        return;
    }

    ROUTE_AUTOCOMPLETE_AVAILABLE = true;

    ORIGIN_AUTOCOMPLETE = new google.maps.places.Autocomplete(originInput, {
        fields: ["place_id", "formatted_address", "name", "geometry"],
        componentRestrictions: { country: "kr" }
    });

    DESTINATION_AUTOCOMPLETE = new google.maps.places.Autocomplete(destinationInput, {
        fields: ["place_id", "formatted_address", "name", "geometry"],
        componentRestrictions: { country: "kr" }
    });

    ORIGIN_AUTOCOMPLETE.addListener("place_changed", () => {
        SELECTED_ORIGIN_PLACE = ORIGIN_AUTOCOMPLETE.getPlace();
        console.log("[Route] 출발지 선택:", SELECTED_ORIGIN_PLACE);
    });

    DESTINATION_AUTOCOMPLETE.addListener("place_changed", () => {
        SELECTED_DESTINATION_PLACE = DESTINATION_AUTOCOMPLETE.getPlace();
        console.log("[Route] 도착지 선택:", SELECTED_DESTINATION_PLACE);
    });

    originInput.addEventListener("input", () => {
        if (!originInput.value.trim()) {
            SELECTED_ORIGIN_PLACE = null;
        }
    });

    destinationInput.addEventListener("input", () => {
        if (!destinationInput.value.trim()) {
            SELECTED_DESTINATION_PLACE = null;
        }
    });
}

function drawKakaoRoutePolyline(path) {
    if (!realtimeMonitorMap) return;

    if (realtimeRoutePolyline) {
        realtimeRoutePolyline.setMap(null);
        realtimeRoutePolyline = null;
    }

    if (!Array.isArray(path) || path.length === 0) {
        return;
    }

    realtimeRoutePolyline = new google.maps.Polyline({
        path: path,
        geodesic: true,
        strokeColor: "#2563eb",
        strokeOpacity: 0.9,
        strokeWeight: 6
    });

    realtimeRoutePolyline.setMap(realtimeMonitorMap);
}

function updateKakaoRouteMeta(distanceM, durationS) {
    const subtitle = document.getElementById("risk-list-subtitle");
    if (!subtitle) return;

    const distanceKm = (Number(distanceM || 0) / 1000).toFixed(1);
    const durationMin = Math.round(Number(durationS || 0) / 60);

    subtitle.textContent = `입력한 이동 경로 주변의 위험 지점을 표시하고 있습니다. 예상 거리 ${distanceKm}km · 예상 시간 ${durationMin}분`;
}

function validateRouteInput(inputValue, label) {
    if (!inputValue) {
        return `${label}를 입력해주세요.`;
    }
    return null;
}

async function requestKakaoRoute(originPlace, destinationPlace) {
    if (!window.REALTIME_MONITOR_CONFIG?.kakaoRouteApiUrl) {
        throw new Error("카카오 경로 API URL이 설정되지 않았습니다.");
    }

    if (!originPlace?.geometry?.location || !destinationPlace?.geometry?.location) {
        throw new Error("출발지/도착지 geometry 정보가 없습니다.");
    }

    const originLat = originPlace.geometry.location.lat();
    const originLng = originPlace.geometry.location.lng();
    const destLat = destinationPlace.geometry.location.lat();
    const destLng = destinationPlace.geometry.location.lng();

    const url = buildApiUrl(window.REALTIME_MONITOR_CONFIG.kakaoRouteApiUrl, {
        origin_lat: originLat,
        origin_lng: originLng,
        dest_lat: destLat,
        dest_lng: destLng
    });

    console.log("[KakaoRoute] 요청 URL:", url);

    const result = await fetchJson(url);

    if (!result.success) {
        throw new Error(result.message || "카카오 경로 조회 실패");
    }

    return result.data;
}

function bindRouteRiskButtons() {
    const findBtn = document.getElementById("find-route-risk-btn");
    const resetBtn = document.getElementById("reset-route-risk-btn");

    if (findBtn) {
        findBtn.addEventListener("click", async () => {
            const originInput = document.getElementById("route-origin");
            const destinationInput = document.getElementById("route-destination");
            const radius = Number(document.getElementById("route-risk-radius")?.value || 0.5);

            const originValue = originInput?.value?.trim() || "";
            const destinationValue = destinationInput?.value?.trim() || "";

            const originError = validateRouteInput(originValue, "출발지");
            if (originError) {
                alert(originError);
                originInput?.focus();
                return;
            }

            const destinationError = validateRouteInput(destinationValue, "도착지");
            if (destinationError) {
                alert(destinationError);
                destinationInput?.focus();
                return;
            }

            if (!SELECTED_ORIGIN_PLACE?.geometry?.location) {
                alert("출발지는 자동완성 목록에서 정확히 선택해주세요.");
                originInput?.focus();
                return;
            }

            if (!SELECTED_DESTINATION_PLACE?.geometry?.location) {
                alert("도착지는 자동완성 목록에서 정확히 선택해주세요.");
                destinationInput?.focus();
                return;
            }

            const originLat = SELECTED_ORIGIN_PLACE.geometry.location.lat();
            const originLng = SELECTED_ORIGIN_PLACE.geometry.location.lng();
            const destLat = SELECTED_DESTINATION_PLACE.geometry.location.lat();
            const destLng = SELECTED_DESTINATION_PLACE.geometry.location.lng();

            if (
                Math.abs(originLat - destLat) < 0.00001 &&
                Math.abs(originLng - destLng) < 0.00001
            ) {
                alert("출발지와 도착지가 동일합니다. 서로 다른 위치를 선택해주세요.");
                return;
            }

            try {
                showLoading("카카오 경로 분석 중...");

                console.log("[KakaoRoute] 출발지:", SELECTED_ORIGIN_PLACE);
                console.log("[KakaoRoute] 도착지:", SELECTED_DESTINATION_PLACE);

                const routeData = await requestKakaoRoute(
                    SELECTED_ORIGIN_PLACE,
                    SELECTED_DESTINATION_PLACE
                );

                const path = routeData.path || [];
                if (!path.length) {
                    alert("카카오 길찾기 결과에 경로 좌표가 없습니다.");
                    return;
                }

                drawKakaoRoutePolyline(path);

                CURRENT_ROUTE_POINTS = path.map((p) => ({
                    lat: Number(p.lat),
                    lng: Number(p.lng)
                }));
                CURRENT_ROUTE_RADIUS_KM = radius;
                CURRENT_ROUTE_ACTIVE = true;

                const title = document.getElementById("risk-list-title");
                const subtitle = document.getElementById("risk-list-subtitle");

                if (title) {
                    title.textContent = "경로 위험 리스트";
                }

                if (subtitle) {
                    subtitle.textContent = "입력한 이동 경로 주변의 위험 지점만 표시하고 있습니다.";
                }

                updateKakaoRouteMeta(routeData.distance_m, routeData.duration_s);
                applyFiltersAndRender({ preserveView: true });
            } catch (error) {
                console.error("[KakaoRoute] 실패:", error);
                alert(error.message || "카카오 길찾기 조회 중 오류가 발생했습니다.");
            } finally {
                hideLoading();
            }
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener("click", () => {
            clearRoute();
            applyFiltersAndRender({ preserveView: true });
        });
    }
}

function initRealtimeMonitorMap() {
    const mapElement = document.getElementById("realtime-monitor-map");
    if (!mapElement) return;

    realtimeMonitorMap = new google.maps.Map(mapElement, {
        center: { lat: 37.5665, lng: 126.9780 },
        zoom: 11,
        mapTypeControl: true,
        fullscreenControl: true,
        streetViewControl: false
    });

    realtimeMonitorInfoWindow = new google.maps.InfoWindow();

    initRouteAutocomplete();

    refreshRealtimeMonitorData({
        preserveView: false,
        showOverlay: true
    });

    setInterval(() => {
        refreshRealtimeMonitorData({
            preserveView: true,
            showOverlay: false
        });
    }, 30000);
}

function getRiskDetailElements() {
    return {
        modal: document.getElementById("risk-detail-modal"),
        backdrop: document.getElementById("risk-detail-backdrop"),
        closeBtn: document.getElementById("risk-detail-close"),

        badge: document.getElementById("risk-detail-badge"),
        timeago: document.getElementById("risk-detail-timeago"),
        title: document.getElementById("risk-detail-title"),
        location: document.getElementById("risk-detail-location"),
        content: document.getElementById("risk-detail-content"),

        reportId: document.getElementById("risk-detail-report-id"),
        detectedLabel: document.getElementById("risk-detail-detected-label"),
        confidence: document.getElementById("risk-detail-confidence"),
        status: document.getElementById("risk-detail-status"),
        reportType: document.getElementById("risk-detail-report-type"),
        createdAt: document.getElementById("risk-detail-created-at"),
        fileType: document.getElementById("risk-detail-file-type"),
        originalName: document.getElementById("risk-detail-original-name"),

        image: document.getElementById("risk-detail-image"),
        imageEmpty: document.getElementById("risk-detail-image-empty")
    };
}

function openModal() {
    const { modal } = getRiskDetailElements();
    if (!modal) return;

    modal.classList.remove("hidden");
    document.body.classList.add("modal-open");
}

function closeModal() {
    const { modal } = getRiskDetailElements();
    if (!modal) return;

    modal.classList.add("hidden");
    document.body.classList.remove("modal-open");
}

function setBadgeStyle(element, riskLevel) {
    if (!element) return;

    element.className = "risk-detail-badge";

    if (riskLevel === "긴급") {
        element.classList.add("emergency");
    } else if (riskLevel === "위험") {
        element.classList.add("danger");
    } else {
        element.classList.add("warning");
    }

    element.textContent = riskLevel || "주의";
}

function renderRiskDetail(detail) {
    const els = getRiskDetailElements();

    setBadgeStyle(els.badge, detail.risk_level);
    if (els.timeago) els.timeago.textContent = detail.time_ago || "-";
    if (els.title) els.title.textContent = detail.title || "제목 없음";
    if (els.location) els.location.textContent = detail.location_text || "위치 정보 없음";
    if (els.content) els.content.textContent = detail.content || "상세 내용 없음";

    if (els.reportId) els.reportId.textContent = detail.report_id ?? "-";
    if (els.detectedLabel) els.detectedLabel.textContent = detail.detected_label || "-";
    if (els.confidence) els.confidence.textContent = detail.confidence ?? "-";
    if (els.status) els.status.textContent = detail.status || "-";
    if (els.reportType) els.reportType.textContent = detail.report_type || "-";
    if (els.createdAt) els.createdAt.textContent = detail.created_at || "-";
    if (els.fileType) els.fileType.textContent = detail.file_type || "-";
    if (els.originalName) els.originalName.textContent = detail.original_name || "-";

    if (els.image && els.imageEmpty) {
        if (detail.file_path && detail.file_type === "이미지") {
            els.image.src = detail.file_path;
            els.image.style.display = "block";
            els.imageEmpty.style.display = "none";
        } else {
            els.image.src = "";
            els.image.style.display = "none";
            els.imageEmpty.style.display = "flex";
        }
    }
}

async function openRiskDetailModal(reportId) {
    if (!window.REALTIME_MONITOR_CONFIG || !reportId) return;

    try {
        showLoading("상세 정보 불러오는 중...");

        const url = `${window.REALTIME_MONITOR_CONFIG.detailApiBaseUrl}/${reportId}`;
        const result = await fetchJson(url);

        if (!result.success) {
            alert(result.message || "상세 정보를 불러오지 못했습니다.");
            return;
        }

        renderRiskDetail(result.data);
        openModal();
    } catch (error) {
        console.error("상세 정보 조회 실패:", error);
        alert("상세 정보를 불러오는 중 오류가 발생했습니다.");
    } finally {
        hideLoading();
    }
}

function bindRiskDetailModalEvents() {
    const { backdrop, closeBtn, modal } = getRiskDetailElements();

    if (backdrop) {
        backdrop.addEventListener("click", closeModal);
    }

    if (closeBtn) {
        closeBtn.addEventListener("click", closeModal);
    }

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && modal && !modal.classList.contains("hidden")) {
            closeModal();
        }
    });

    document.querySelectorAll(".risk-list-item[data-report-id]").forEach((item) => {
        item.addEventListener("click", () => {
            const reportId = item.dataset.reportId;
            if (reportId) {
                openRiskDetailModal(reportId);
            }
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const configuredDays = Number(document.body?.dataset?.realtimeVisibleDays || 180);
    CURRENT_VISIBLE_DAYS = Number.isNaN(configuredDays) ? 180 : configuredDays;

    bindRiskFilterButtons();
    bindRadiusSelect();
    bindSortSelect();
    bindNearbyButtons();
    bindRouteRiskButtons();
    bindRiskDetailModalEvents();
    hideRouteSummary();
});

window.initRealtimeMonitorMap = initRealtimeMonitorMap;