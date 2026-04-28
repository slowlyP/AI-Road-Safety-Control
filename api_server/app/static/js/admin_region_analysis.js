let regionAnalysisMap = null;
let regionMarkers = [];
let labelChartInstance = null;
let riskChartInstance = null;
let regionInfoWindow = null;
let regionHeatmap = null;
let currentMapView = "marker";
let latestPointData = [];

let rockRouteAutocompleteOrigin = null;
let rockRouteAutocompleteDestination = null;
let selectedRockRouteOrigin = null;
let selectedRockRouteDestination = null;
let rockRoutePolyline = null;

let rockRouteAllItems = [];
let rockRouteCurrentPage = 1;
const ROCK_ROUTE_PAGE_SIZE = 5;

function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value ?? "";
    return div.innerHTML;
}

function clearRegionMarkers() {
    regionMarkers.forEach((marker) => marker.setMap(null));
    regionMarkers = [];
}

function clearHeatmap() {
    if (regionHeatmap) {
        regionHeatmap.setMap(null);
        regionHeatmap = null;
    }
}

function clearRockRoutePolyline() {
    if (rockRoutePolyline) {
        rockRoutePolyline.setMap(null);
        rockRoutePolyline = null;
    }
}

function getMarkerColorByRiskLevel(riskLevel) {
    if (riskLevel === "긴급") return "http://maps.google.com/mapfiles/ms/icons/red-dot.png";
    if (riskLevel === "위험") return "http://maps.google.com/mapfiles/ms/icons/orange-dot.png";
    return "http://maps.google.com/mapfiles/ms/icons/yellow-dot.png";
}

function getHeatmapWeightByRiskLevel(riskLevel) {
    if (riskLevel === "긴급") return 5;
    if (riskLevel === "위험") return 3;
    return 1;
}

function buildDataUrl() {
    const baseUrl = window.REGION_ANALYSIS_CONFIG.dataApiUrl;
    const days = document.getElementById("analysis-days")?.value || "30";
    const label = document.getElementById("analysis-label")?.value || "all";
    const riskLevel = document.getElementById("analysis-risk-level")?.value || "all";

    const url = new URL(baseUrl, window.location.origin);
    url.searchParams.set("days", days);
    url.searchParams.set("label", label);
    url.searchParams.set("risk_level", riskLevel);

    return url.toString();
}

function buildRockRouteAnalysisUrl() {
    return `${window.REGION_ANALYSIS_CONFIG.dataApiUrl.replace("/data", "/rock-route-analysis")}`;
}

async function fetchRegionAnalysisData() {
    const response = await fetch(buildDataUrl(), {
        method: "GET",
        headers: {
            "X-Requested-With": "XMLHttpRequest"
        }
    });

    const result = await response.json();

    if (!response.ok || !result.success) {
        throw new Error(result.message || "위험 지역 분석 데이터 조회 실패");
    }

    return result.data;
}

async function requestRockRouteAnalysis(path, days = 30, radiusKm = 2) {
    const response = await fetch(buildRockRouteAnalysisUrl(), {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        },
        body: JSON.stringify({
            path: path,
            days: days,
            radius_km: radiusKm
        })
    });

    const result = await response.json();

    if (!response.ok || !result.success) {
        throw new Error(result.message || "범위 낙석 분석 실패");
    }

    return result.data;
}

async function requestKakaoRoute(originPlace, destinationPlace) {
    const originLat = originPlace.geometry.location.lat();
    const originLng = originPlace.geometry.location.lng();
    const destLat = destinationPlace.geometry.location.lat();
    const destLng = destinationPlace.geometry.location.lng();

    const url = new URL("/api/navigation/kakao-route", window.location.origin);
    url.searchParams.set("origin_lat", originLat);
    url.searchParams.set("origin_lng", originLng);
    url.searchParams.set("dest_lat", destLat);
    url.searchParams.set("dest_lng", destLng);

    const response = await fetch(url.toString(), {
        method: "GET",
        headers: {
            "X-Requested-With": "XMLHttpRequest"
        }
    });

    const result = await response.json();

    if (!response.ok || !result.success) {
        throw new Error(result.message || "카카오 경로 조회 실패");
    }

    return result.data;
}

function updateSummary(summary) {
    const totalIncidentsEl = document.getElementById("summary-total-incidents");
    const hotspotRegionsEl = document.getElementById("summary-hotspot-regions");
    const rockRatioEl = document.getElementById("summary-rock-ratio");
    const emergencyCountEl = document.getElementById("summary-emergency-count");

    if (totalIncidentsEl) totalIncidentsEl.textContent = summary.total_incidents ?? 0;
    if (hotspotRegionsEl) hotspotRegionsEl.textContent = summary.hotspot_regions ?? 0;
    if (rockRatioEl) rockRatioEl.textContent = `${summary.rock_ratio ?? 0}%`;
    if (emergencyCountEl) emergencyCountEl.textContent = summary.emergency_count ?? 0;
}

function renderDistrictSummary(items) {
    const container = document.getElementById("district-summary-grid");
    if (!container) return;

    if (!items || items.length === 0) {
        container.innerHTML = `<div class="district-empty">집계 가능한 지역 데이터가 없습니다.</div>`;
        return;
    }

    container.innerHTML = items.map((item) => `
        <div class="district-card">
            <div class="district-card-top">
                <span class="district-name">${escapeHtml(item.district_name)}</span>
                <span class="district-risk-badge risk-${escapeHtml(item.max_risk_level)}">${escapeHtml(item.max_risk_level)}</span>
            </div>
            <div class="district-card-main">${item.incident_count}</div>
            <div class="district-card-label">전체 사고 건수</div>
            <div class="district-card-meta">
                <span>긴급 ${item.emergency_count}건</span>
                <span>낙석 ${item.rock_count}건</span>
            </div>
        </div>
    `).join("");
}

function renderTopRegions(items) {
    const container = document.getElementById("top-region-list");
    if (!container) return;

    if (!items || items.length === 0) {
        container.innerHTML = `
            <div class="top-region-empty">
                현재 조건에 맞는 지역 데이터가 없습니다.
            </div>
        `;
        return;
    }

    container.innerHTML = items.map((item, index) => `
        <div class="top-region-item">
            <div class="top-region-rank">${index + 1}</div>
            <div class="top-region-content">
                <div class="top-region-title">${escapeHtml(item.location_text)}</div>
                <div class="top-region-meta">
                    <span>사고 ${item.incident_count}건</span>
                    <span>최대 위험도 ${escapeHtml(item.max_risk_level)}</span>
                </div>
            </div>
        </div>
    `).join("");
}

function buildBounds(points) {
    const bounds = new google.maps.LatLngBounds();
    let validCount = 0;

    points.forEach((item) => {
        const lat = Number(item.latitude);
        const lng = Number(item.longitude);

        if (!lat || !lng) return;

        bounds.extend({ lat, lng });
        validCount += 1;
    });

    return { bounds, validCount };
}

function fitMapToPoints(points) {
    if (!regionAnalysisMap) return;

    const { bounds, validCount } = buildBounds(points);

    if (validCount > 0) {
        regionAnalysisMap.fitBounds(bounds);

        const listener = google.maps.event.addListener(regionAnalysisMap, "idle", function () {
            if (regionAnalysisMap.getZoom() > 14) {
                regionAnalysisMap.setZoom(14);
            }
            google.maps.event.removeListener(listener);
        });
    } else {
        regionAnalysisMap.setCenter({ lat: 37.5665, lng: 126.9780 });
        regionAnalysisMap.setZoom(11);
    }
}

function renderMarkers(points) {
    if (!regionAnalysisMap) return;

    clearRegionMarkers();

    if (!regionInfoWindow) {
        regionInfoWindow = new google.maps.InfoWindow();
    }

    points.forEach((item) => {
        const lat = Number(item.latitude);
        const lng = Number(item.longitude);

        if (!lat || !lng) return;

        const marker = new google.maps.Marker({
            position: { lat, lng },
            map: regionAnalysisMap,
            title: item.location_text || "위치 정보 없음",
            icon: getMarkerColorByRiskLevel(item.risk_level)
        });

        marker.addListener("click", () => {
            regionInfoWindow.setContent(`
                <div style="min-width:240px; line-height:1.6;">
                    <div style="font-weight:800; margin-bottom:8px;">
                        ${escapeHtml(item.location_text || "위치 정보 없음")}
                    </div>
                    <div><strong>시군구:</strong> ${escapeHtml(item.district_name || "-")}</div>
                    <div><strong>사고명:</strong> ${escapeHtml(item.title || "-")}</div>
                    <div><strong>유형:</strong> ${escapeHtml(item.detected_label_kor || "-")}</div>
                    <div><strong>위험도:</strong> ${escapeHtml(item.risk_level || "-")}</div>
                    <div><strong>상태:</strong> ${escapeHtml(item.status || "-")}</div>
                    <div><strong>신뢰도:</strong> ${escapeHtml(String(item.confidence ?? "-"))}</div>
                    <div><strong>발생 시각:</strong> ${escapeHtml(item.created_at || "-")}</div>
                </div>
            `);

            regionInfoWindow.open({
                anchor: marker,
                map: regionAnalysisMap
            });
        });

        regionMarkers.push(marker);
    });
}

function renderHeatmap(points) {
    if (!regionAnalysisMap || !google.maps.visualization) return;

    clearHeatmap();

    const heatmapData = points
        .map((item) => {
            const lat = Number(item.latitude);
            const lng = Number(item.longitude);

            if (!lat || !lng) return null;

            return {
                location: new google.maps.LatLng(lat, lng),
                weight: getHeatmapWeightByRiskLevel(item.risk_level)
            };
        })
        .filter(Boolean);

    regionHeatmap = new google.maps.visualization.HeatmapLayer({
        data: heatmapData,
        dissipating: true,
        radius: 30,
        opacity: 0.8
    });

    regionHeatmap.setMap(regionAnalysisMap);
}

function applyMapView(points) {
    if (!regionAnalysisMap) return;

    clearRegionMarkers();
    clearHeatmap();

    if (currentMapView === "heatmap") {
        renderHeatmap(points);
    } else {
        renderMarkers(points);
    }

    fitMapToPoints(points);
}

function updateMapViewButtons() {
    document.querySelectorAll(".map-view-btn").forEach((btn) => {
        const view = btn.dataset.mapView;
        if (view === currentMapView) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });
}

function renderLabelChart(items) {
    const canvas = document.getElementById("label-distribution-chart");
    if (!canvas) return;

    if (labelChartInstance) {
        labelChartInstance.destroy();
    }

    labelChartInstance = new Chart(canvas, {
        type: "bar",
        data: {
            labels: items.map((item) => item.label_kor),
            datasets: [{
                label: "사고 수",
                data: items.map((item) => item.count)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: "#ffffff" }
                }
            },
            scales: {
                x: {
                    ticks: { color: "#bfc9dc" },
                    grid: { color: "rgba(255,255,255,0.08)" }
                },
                y: {
                    beginAtZero: true,
                    ticks: { color: "#bfc9dc" },
                    grid: { color: "rgba(255,255,255,0.08)" }
                }
            }
        }
    });
}

function renderRiskChart(items) {
    const canvas = document.getElementById("risk-distribution-chart");
    if (!canvas) return;

    if (riskChartInstance) {
        riskChartInstance.destroy();
    }

    riskChartInstance = new Chart(canvas, {
        type: "doughnut",
        data: {
            labels: items.map((item) => item.risk_level),
            datasets: [{
                data: items.map((item) => item.count)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: "#ffffff" }
                }
            }
        }
    });
}

function initRockRouteAutocomplete() {
    const originInput = document.getElementById("rock-route-origin");
    const destinationInput = document.getElementById("rock-route-destination");

    if (!originInput || !destinationInput) return;
    if (!google.maps.places || !google.maps.places.Autocomplete) return;

    rockRouteAutocompleteOrigin = new google.maps.places.Autocomplete(originInput, {
        fields: ["place_id", "formatted_address", "name", "geometry"],
        componentRestrictions: { country: "kr" }
    });

    rockRouteAutocompleteDestination = new google.maps.places.Autocomplete(destinationInput, {
        fields: ["place_id", "formatted_address", "name", "geometry"],
        componentRestrictions: { country: "kr" }
    });

    rockRouteAutocompleteOrigin.addListener("place_changed", () => {
        selectedRockRouteOrigin = rockRouteAutocompleteOrigin.getPlace();
    });

    rockRouteAutocompleteDestination.addListener("place_changed", () => {
        selectedRockRouteDestination = rockRouteAutocompleteDestination.getPlace();
    });

    originInput.addEventListener("input", () => {
        if (!originInput.value.trim()) {
            selectedRockRouteOrigin = null;
        }
    });

    destinationInput.addEventListener("input", () => {
        if (!destinationInput.value.trim()) {
            selectedRockRouteDestination = null;
        }
    });
}

function drawRockRoutePolyline(path) {
    if (!regionAnalysisMap) return;

    clearRockRoutePolyline();

    if (!Array.isArray(path) || path.length === 0) return;

    rockRoutePolyline = new google.maps.Polyline({
        path: path,
        geodesic: true,
        strokeColor: "#22c55e",
        strokeOpacity: 0.95,
        strokeWeight: 6
    });

    rockRoutePolyline.setMap(regionAnalysisMap);
}

function updateRockRouteSummary(summary) {
    const countEl = document.getElementById("rock-route-count");
    const emergencyEl = document.getElementById("rock-route-emergency-count");
    const districtEl = document.getElementById("rock-route-top-district");
    const districtCountEl = document.getElementById("rock-route-top-district-count");
    const messageEl = document.getElementById("rock-route-message");

    if (countEl) countEl.textContent = summary.rock_count ?? 0;
    if (emergencyEl) emergencyEl.textContent = summary.emergency_rock_count ?? 0;
    if (districtEl) districtEl.textContent = summary.top_district || "-";
    if (districtCountEl) districtCountEl.textContent = `낙석 ${summary.top_district_count ?? 0}건`;
    if (messageEl) messageEl.textContent = summary.risk_message || "";
}

function bindRockRouteResultClickEvents() {
    document.querySelectorAll(".rock-route-result-item[data-report-id]").forEach((itemEl) => {
        itemEl.addEventListener("click", () => {
            const reportId = itemEl.dataset.reportId;
            if (!reportId) return;

            window.location.href = `/admin/reports/${reportId}`;
        });
    });
}

function renderRockRoutePagination(totalPages) {
    const paginationEl = document.getElementById("rock-route-pagination");
    if (!paginationEl) return;

    if (totalPages <= 1) {
        paginationEl.innerHTML = "";
        return;
    }

    let html = "";

    html += `
        <button
            type="button"
            class="rock-route-page-btn"
            ${rockRouteCurrentPage === 1 ? "disabled" : ""}
            data-page="${rockRouteCurrentPage - 1}"
        >
            이전
        </button>
    `;

    for (let i = 1; i <= totalPages; i++) {
        html += `
            <button
                type="button"
                class="rock-route-page-btn ${i === rockRouteCurrentPage ? "active" : ""}"
                data-page="${i}"
            >
                ${i}
            </button>
        `;
    }

    html += `
        <button
            type="button"
            class="rock-route-page-btn"
            ${rockRouteCurrentPage === totalPages ? "disabled" : ""}
            data-page="${rockRouteCurrentPage + 1}"
        >
            다음
        </button>
    `;

    paginationEl.innerHTML = html;

    paginationEl.querySelectorAll(".rock-route-page-btn[data-page]").forEach((btn) => {
        if (btn.disabled) return;

        btn.addEventListener("click", () => {
            const page = Number(btn.dataset.page || 1);
            renderRockRouteResultList(rockRouteAllItems, page);
        });
    });
}

function renderRockRouteResultList(items, page = 1) {
    const container = document.getElementById("rock-route-result-list");
    const paginationEl = document.getElementById("rock-route-pagination");

    if (!container) return;

    rockRouteAllItems = Array.isArray(items) ? items : [];
    rockRouteCurrentPage = page;

    if (!rockRouteAllItems.length) {
        container.innerHTML = `
            <div class="top-region-empty">
                선택한 검색 범위 주변에서 확인된 낙석 사고가 없습니다.
            </div>
        `;

        if (paginationEl) {
            paginationEl.innerHTML = "";
        }
        return;
    }

    const totalPages = Math.ceil(rockRouteAllItems.length / ROCK_ROUTE_PAGE_SIZE);
    const startIndex = (rockRouteCurrentPage - 1) * ROCK_ROUTE_PAGE_SIZE;
    const endIndex = startIndex + ROCK_ROUTE_PAGE_SIZE;
    const pagedItems = rockRouteAllItems.slice(startIndex, endIndex);

    container.innerHTML = pagedItems.map((item, index) => `
        <div class="top-region-item rock-route-result-item" data-report-id="${item.report_id}">
            <div class="top-region-rank">${startIndex + index + 1}</div>
            <div class="top-region-content">
                <div class="top-region-title">${escapeHtml(item.location_text)}</div>
                <div class="top-region-meta">
                    <span>${escapeHtml(item.district_name)}</span>
                    <span>위험도 ${escapeHtml(item.risk_level)}</span>
                    <span>신뢰도 ${escapeHtml(String(item.confidence ?? "-"))}</span>
                    <span>${escapeHtml(item.created_at)}</span>
                </div>
            </div>
        </div>
    `).join("");

    bindRockRouteResultClickEvents();
    renderRockRoutePagination(totalPages);
}

async function analyzeRockRoute() {
    const days = Number(document.getElementById("rock-route-days")?.value || 30);

    if (!selectedRockRouteOrigin?.geometry?.location) {
        alert("검색 시작 지점을 자동완성 목록에서 선택해주세요.");
        return;
    }

    if (!selectedRockRouteDestination?.geometry?.location) {
        alert("검색 종료 지점을 자동완성 목록에서 선택해주세요.");
        return;
    }

    try {
        const routeData = await requestKakaoRoute(
            selectedRockRouteOrigin,
            selectedRockRouteDestination
        );

        const path = routeData.path || [];
        if (!Array.isArray(path) || path.length === 0) {
            alert("검색 범위 좌표를 불러오지 못했습니다.");
            return;
        }

        drawRockRoutePolyline(path);

        const analysisData = await requestRockRouteAnalysis(path, days, 2);

        updateRockRouteSummary(analysisData.summary || {});
        renderRockRouteResultList(analysisData.items || [], 1);
    } catch (error) {
        console.error("[RockRouteAnalysis] error:", error);
        alert(error.message || "범위 낙석 분석 중 오류가 발생했습니다.");
    }
}

function resetRockRouteAnalysis() {
    const originInput = document.getElementById("rock-route-origin");
    const destinationInput = document.getElementById("rock-route-destination");
    const daysSelect = document.getElementById("rock-route-days");
    const paginationEl = document.getElementById("rock-route-pagination");

    if (originInput) originInput.value = "";
    if (destinationInput) destinationInput.value = "";
    if (daysSelect) daysSelect.value = "30";

    selectedRockRouteOrigin = null;
    selectedRockRouteDestination = null;
    rockRouteAllItems = [];
    rockRouteCurrentPage = 1;

    clearRockRoutePolyline();

    updateRockRouteSummary({
        rock_count: 0,
        emergency_rock_count: 0,
        top_district: "-",
        top_district_count: 0,
        risk_message: "검색 범위를 선택하면 낙석 위험 분석 결과가 표시됩니다."
    });

    renderRockRouteResultList([], 1);

    if (paginationEl) {
        paginationEl.innerHTML = "";
    }
}

async function refreshRegionAnalysis() {
    try {
        const data = await fetchRegionAnalysisData();

        latestPointData = data.points || [];

        updateSummary(data.summary || {});
        renderDistrictSummary(data.district_summary || []);
        renderTopRegions(data.top_regions || []);
        applyMapView(latestPointData);
        updateMapViewButtons();
        renderLabelChart(data.label_distribution || []);
        renderRiskChart(data.risk_distribution || []);
    } catch (error) {
        console.error("[RegionAnalysis] refresh error:", error);
        alert("위험 지역 분석 데이터를 불러오는 중 오류가 발생했습니다.");
    }
}

function bindRegionAnalysisEvents() {
    const applyBtn = document.getElementById("analysis-apply-btn");
    if (applyBtn) {
        applyBtn.addEventListener("click", refreshRegionAnalysis);
    }

    document.querySelectorAll(".map-view-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            currentMapView = btn.dataset.mapView || "marker";
            updateMapViewButtons();
            applyMapView(latestPointData);
        });
    });

    const rockAnalyzeBtn = document.getElementById("rock-route-analyze-btn");
    if (rockAnalyzeBtn) {
        rockAnalyzeBtn.addEventListener("click", analyzeRockRoute);
    }

    const rockResetBtn = document.getElementById("rock-route-reset-btn");
    if (rockResetBtn) {
        rockResetBtn.addEventListener("click", resetRockRouteAnalysis);
    }
}

function initRegionAnalysisMap() {
    const mapElement = document.getElementById("region-analysis-map");
    if (!mapElement) return;

    regionAnalysisMap = new google.maps.Map(mapElement, {
        center: { lat: 37.5665, lng: 126.9780 },
        zoom: 11,
        mapTypeControl: true,
        fullscreenControl: true,
        streetViewControl: false
    });

    const initialData = window.REGION_ANALYSIS_CONFIG.initialData || {};
    latestPointData = initialData.points || [];

    updateSummary(initialData.summary || {});
    renderDistrictSummary(initialData.district_summary || []);
    renderTopRegions(initialData.top_regions || []);
    updateMapViewButtons();
    applyMapView(latestPointData);
    renderLabelChart(initialData.label_distribution || []);
    renderRiskChart(initialData.risk_distribution || []);
    initRockRouteAutocomplete();
}

document.addEventListener("DOMContentLoaded", () => {
    bindRegionAnalysisEvents();
    resetRockRouteAnalysis();
});

window.initRegionAnalysisMap = initRegionAnalysisMap;