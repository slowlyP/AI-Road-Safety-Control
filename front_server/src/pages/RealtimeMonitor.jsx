import React, { useState, useEffect, useRef, useCallback } from 'react';
import '../styles/RealtimeMonitor.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

const RealtimeMonitor = () => {
  const [summary, setSummary] = useState({
    current_risk_zones: 0,
    today_reports: 0,
    emergency_last_24h: 0,
    hotspots: 0
  });
  const [riskList, setRiskList] = useState([]);
  const [filteredRiskList, setFilteredRiskList] = useState([]);
  const [mapPoints, setMapPoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [riskFilter, setRiskFilter] = useState('all');
  const [sortType, setSortType] = useState('risk_desc');
  const [selectedReport, setSelectedReport] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markersRef = useRef([]);
  const infoWindowRef = useRef(null);

  // 데이터 로드
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [summaryRes, pointsRes, listRes] = await Promise.all([
        fetch(`${API_BASE_URL}/realtime-monitor/summary`),
        fetch(`${API_BASE_URL}/realtime-monitor/map-points`),
        fetch(`${API_BASE_URL}/realtime-monitor/risk-list`)
      ]);

      const summaryData = await summaryRes.json();
      const pointsData = await pointsRes.json();
      const listData = await listRes.json();

      if (summaryData.success) setSummary(summaryData.data);
      if (pointsData.success) setMapPoints(pointsData.items);
      if (listData.success) setRiskList(listData.items);
    } catch (error) {
      console.error("Failed to load monitor data:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  // 지도 초기화
  useEffect(() => {
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${import.meta.env.VITE_GOOGLE_MAPS_API_KEY}&libraries=places`;
    script.async = true;
    script.defer = true;
    script.onload = () => {
      if (mapRef.current && !mapInstance.current) {
        mapInstance.current = new window.google.maps.Map(mapRef.current, {
          center: { lat: 37.5665, lng: 126.9780 },
          zoom: 12,
          styles: [
            { elementType: "geometry", stylers: [{ color: "#242f3e" }] },
            { elementType: "labels.text.stroke", stylers: [{ color: "#242f3e" }] },
            { elementType: "labels.text.fill", stylers: [{ color: "#746855" }] },
            // ... (기타 다크모드 스타일 생략 가능)
          ]
        });
        infoWindowRef.current = new window.google.maps.InfoWindow();
        loadData();
      }
    };
    document.head.appendChild(script);

    return () => {
      // 컴포넌트 언마운트 시 스크립트 제거 로직 등 (필요 시)
    };
  }, [loadData]);

  // 필터링 및 정렬 적용
  useEffect(() => {
    let filtered = [...riskList];
    if (riskFilter !== 'all') {
      filtered = filtered.filter(item => item.risk_level === riskFilter);
    }

    filtered.sort((a, b) => {
      if (sortType === 'risk_desc') {
        const priority = { '긴급': 3, '위험': 2, '주의': 1 };
        return (priority[b.risk_level] || 0) - (priority[a.risk_level] || 0);
      } else if (sortType === 'latest') {
        return new Date(b.created_at) - new Date(a.created_at);
      }
      return 0;
    });

    setFilteredRiskList(filtered);
  }, [riskList, riskFilter, sortType]);

  // 마커 렌더링
  useEffect(() => {
    if (!mapInstance.current) return;

    // 기존 마커 제거
    markersRef.current.forEach(marker => marker.setMap(null));
    markersRef.current = [];

    const bounds = new window.google.maps.LatLngBounds();
    let hasPoints = false;

    mapPoints.forEach(point => {
      if (riskFilter !== 'all' && point.risk_level !== riskFilter) return;

      const marker = new window.google.maps.Marker({
        position: { lat: Number(point.latitude), lng: Number(point.longitude) },
        map: mapInstance.current,
        title: point.location_text,
        icon: getMarkerIcon(point.risk_level)
      });

      marker.addListener('click', () => {
        handleMarkerClick(point);
      });

      markersRef.current.push(marker);
      bounds.extend(marker.getPosition());
      hasPoints = true;
    });

    if (hasPoints) {
      mapInstance.current.fitBounds(bounds);
    }
  }, [mapPoints, riskFilter]);

  const getMarkerIcon = (level) => {
    switch (level) {
      case '긴급': return 'http://maps.google.com/mapfiles/ms/icons/red-dot.png';
      case '위험': return 'http://maps.google.com/mapfiles/ms/icons/orange-dot.png';
      default: return 'http://maps.google.com/mapfiles/ms/icons/yellow-dot.png';
    }
  };

  const handleMarkerClick = async (point) => {
    try {
      const res = await fetch(`${API_BASE_URL}/realtime-monitor/detail/${point.report_id}`);
      const data = await res.json();
      if (data.success) {
        setSelectedReport(data.data);
        setIsModalOpen(true);
      }
    } catch (error) {
      console.error("Failed to load detail:", error);
    }
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedReport(null);
  };

  return (
    <div className="monitor-container">
      {/* Summary Cards */}
      <div className="monitor-summary-grid">
        <div className="monitor-summary-card">
          <div className="summary-card-label">현재 위험 구간 수</div>
          <div className="summary-card-value">{summary.current_risk_zones}</div>
          <div className="summary-card-sub">현재 접수/확인중/처리완료 기준</div>
        </div>
        <div className="monitor-summary-card">
          <div className="summary-card-label">오늘 접수 건수</div>
          <div className="summary-card-value">{summary.today_reports}</div>
          <div className="summary-card-sub">오늘 등록된 전체 신고</div>
        </div>
        <div className="monitor-summary-card emergency">
          <div className="summary-card-label">최근 24시간 긴급</div>
          <div className="summary-card-value">{summary.emergency_last_24h}</div>
          <div className="summary-card-sub">즉시 대응 필요</div>
        </div>
        <div className="monitor-summary-card hotspot">
          <div className="summary-card-label">사고 다발 구간</div>
          <div className="summary-card-value">{summary.hotspots}</div>
          <div className="summary-card-sub">최근 7일 반복 발생</div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="monitor-filter-bar">
        <div className="monitor-filter-left">
          {['all', '긴급', '위험', '주의'].map(level => (
            <button
              key={level}
              className={`filter-btn ${riskFilter === level ? 'active' : ''}`}
              onClick={() => setRiskFilter(level)}
            >
              {level === 'all' ? '전체' : level}
            </button>
          ))}
        </div>
        <div className="monitor-filter-right">
          <select 
            className="radius-select"
            value={sortType}
            onChange={(e) => setSortType(e.target.value)}
          >
            <option value="risk_desc">위험도 높은 순</option>
            <option value="latest">최신순</option>
          </select>
        </div>
      </div>

      <div className="monitor-main-grid">
        <div className="monitor-map-panel">
          <div className="monitor-panel-header">
            <h2>지도 기반 위험 현황</h2>
            <p>실시간으로 탐지된 위험 위치를 확인하세요.</p>
          </div>
          <div ref={mapRef} className="realtime-monitor-map"></div>
          <div className="monitor-map-legend">
            <span className="legend-item"><span className="legend-dot emergency"></span> 긴급</span>
            <span className="legend-item"><span className="legend-dot danger"></span> 위험</span>
            <span className="legend-item"><span className="legend-dot warning"></span> 주의</span>
          </div>
        </div>

        <div className="monitor-list-panel">
          <div className="monitor-panel-header">
            <h2>실시간 위험 리스트</h2>
            <p>최근 탐지된 이벤트를 확인하세요.</p>
          </div>
          <div className="realtime-risk-list">
            {filteredRiskList.map(item => (
              <div 
                key={item.report_id} 
                className={`risk-list-item risk-${item.risk_level}`}
                onClick={() => handleMarkerClick(item)}
              >
                <div className="risk-list-top">
                  <span className={`risk-badge risk-${item.risk_level}`}>{item.risk_level}</span>
                  <span className="risk-time">{item.time_ago}</span>
                </div>
                <div className="risk-location">{item.location_text}</div>
                <div className="risk-meta">
                  <span>장애물: {item.detected_label}</span>
                  <span>상태: {item.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Detail Modal */}
      {isModalOpen && selectedReport && (
        <div className="risk-detail-modal">
          <div className="risk-detail-backdrop" onClick={closeModal}></div>
          <div className="risk-detail-dialog">
            <button className="risk-detail-close" onClick={closeModal}>&times;</button>
            <div className="risk-detail-grid">
              <div className="risk-detail-media-panel">
                <div className="risk-detail-media-wrap">
                  {selectedReport.report_files && selectedReport.report_files.length > 0 ? (
                    <img 
                      src={`${API_BASE_URL}/${selectedReport.report_files[0].file_path}`} 
                      className="risk-detail-image" 
                      alt="Detail"
                    />
                  ) : (
                    <div className="risk-detail-image-empty">이미지가 없습니다.</div>
                  )}
                </div>
              </div>
              <div className="risk-detail-info-panel">
                <div className="risk-detail-header">
                  <span className={`risk-detail-badge ${selectedReport.risk_level}`}>{selectedReport.risk_level}</span>
                </div>
                <h2 className="risk-detail-title">{selectedReport.title || '상세 정보'}</h2>
                <p className="risk-detail-location">{selectedReport.location_text}</p>
                <div className="risk-detail-desc">{selectedReport.description}</div>
                <div className="risk-detail-info-list">
                  <div className="risk-detail-info-item">
                    <span className="label">신고 ID</span>
                    <span className="value">{selectedReport.id}</span>
                  </div>
                  <div className="risk-detail-info-item">
                    <span className="label">처리 상태</span>
                    <span className="value">{selectedReport.status}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="loading-overlay">
          <div className="loading-box">
            <div className="loading-spinner"></div>
            <div className="loading-text">데이터를 불러오는 중...</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RealtimeMonitor;
