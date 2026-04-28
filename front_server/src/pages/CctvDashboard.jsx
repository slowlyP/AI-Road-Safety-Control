import React, { useState, useEffect } from 'react';
import ReactPlayer from 'react-player';
import '../styles/CctvDashboard.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';
const CAM_SERVER_URL = import.meta.env.VITE_CAM_SERVER_URL || 'http://localhost:5003';

const localCameras = [
  { id: 0, name: 'Main Gate' },
  { id: 1, name: 'Intersection A' },
  { id: 2, name: 'Highway B' },
  { id: 3, name: 'Parking Lot' }
];

const CctvDashboard = () => {
  const [selectedLocalCam, setSelectedLocalCam] = useState(localCameras[0]);

  const [itsCameras, setItsCameras] = useState([]);
  const [regions, setRegions] = useState([]);
  const [selectedRegion, setSelectedRegion] = useState('');
  const [filteredItsCameras, setFilteredItsCameras] = useState([]);
  const [selectedItsCam, setSelectedItsCam] = useState(null);

  const [isLoadingIts, setIsLoadingIts] = useState(true);
  const [itsError, setItsError] = useState(null);

  useEffect(() => {
    fetchItsCameras();
  }, []);

  const fetchItsCameras = async () => {
    setIsLoadingIts(true);
    try {
      const res = await fetch(`${API_BASE_URL}/cctv/api/its`);
      const data = await res.json();

      if (data.success && data.items && data.items.length > 0) {
        setItsCameras(data.items);

        // Extract regions from cctvname (e.g., "[경부선] 양재IC" -> "경부선")
        const extractedRegions = new Set();
        data.items.forEach(cam => {
          let region = '기타';
          const match = cam.cctvname.match(/^\[(.*?)\]/);
          if (match && match[1]) {
            region = match[1];
          } else if (cam.cctvname.includes(' ')) {
            region = cam.cctvname.split(' ')[0];
          }
          extractedRegions.add(region);
          cam.region = region; // add region property for filtering
        });

        const sortedRegions = Array.from(extractedRegions).sort();
        setRegions(sortedRegions);

        if (sortedRegions.length > 0) {
          const initialRegion = sortedRegions[0];
          setSelectedRegion(initialRegion);
          const initialFiltered = data.items.filter(c => c.region === initialRegion);
          setFilteredItsCameras(initialFiltered);
          if (initialFiltered.length > 0) {
            setSelectedItsCam(initialFiltered[0]);
          }
        }
      } else {
        setItsError("ITS CCTV 데이터를 불러올 수 없습니다.");
      }
    } catch (err) {
      console.error("ITS API fetch error:", err);
      setItsError("ITS 서버 연결 중 오류가 발생했습니다.");
    } finally {
      setIsLoadingIts(false);
    }
  };

  const handleRegionChange = (e) => {
    const region = e.target.value;
    setSelectedRegion(region);
    const filtered = itsCameras.filter(c => c.region === region);
    setFilteredItsCameras(filtered);
    if (filtered.length > 0) {
      setSelectedItsCam(filtered[0]);
    } else {
      setSelectedItsCam(null);
    }
  };

  const handleItsCamChange = (e) => {
    const camUrl = e.target.value;
    const cam = filteredItsCameras.find(c => c.cctvurl === camUrl);
    if (cam) setSelectedItsCam(cam);
  };

  return (
    <div className="cctv-container">
      <div className="cctv-header">
        <h2>실시간 CCTV 대시보드</h2>
        <p>현장 IP 카메라 및 ITS 고속도로 CCTV를 모니터링합니다.</p>
      </div>

      <div className="cctv-split-layout">

        {/* Left: Local IP Camera */}
        <div className="cctv-panel">
          <div className="cctv-panel-header">
            <h3><span className="live-dot"></span> 현장 카메라 (IP Cam)</h3>
            <div className="cctv-controls">
              <select
                className="cctv-dropdown"
                value={selectedLocalCam.id}
                onChange={(e) => {
                  const cam = localCameras.find(c => c.id === parseInt(e.target.value));
                  if (cam) setSelectedLocalCam(cam);
                }}
              >
                {localCameras.map(cam => (
                  <option key={cam.id} value={cam.id}>{cam.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="cctv-player-wrapper">
            <img
              key={selectedLocalCam.id} // force re-render on change
              src={`${CAM_SERVER_URL}/stream/${selectedLocalCam.id}`}
              alt={`Stream ${selectedLocalCam.name}`}
              className="cctv-video-stream"
              onError={(e) => {
                e.target.onerror = null;
                e.target.closest('.cctv-player-wrapper').classList.add('error-state');
              }}
              onLoad={(e) => {
                e.target.closest('.cctv-player-wrapper').classList.remove('error-state');
              }}
            />
            <div className="cctv-error-msg">
              <i className="fa-solid fa-video-slash"></i>
              <p>카메라 연결이 끊어졌습니다</p>
            </div>
            <div className="cctv-overlay-info">
              {selectedLocalCam.name}
            </div>
          </div>
        </div>

        {/* Right: ITS Highway CCTV */}
        <div className="cctv-panel">
          <div className="cctv-panel-header">
            <h3><span className="live-dot its"></span> 고속도로 CCTV (ITS)</h3>
            <div className="cctv-controls multi-controls">
              <select
                className="cctv-dropdown region-select"
                value={selectedRegion}
                onChange={handleRegionChange}
                disabled={isLoadingIts || itsError}
              >
                <option value="" disabled>지역/노선 선택</option>
                {regions.map((reg, idx) => (
                  <option key={idx} value={reg}>{reg}</option>
                ))}
              </select>

              <select
                className="cctv-dropdown cam-select"
                value={selectedItsCam ? selectedItsCam.cctvurl : ''}
                onChange={handleItsCamChange}
                disabled={isLoadingIts || itsError || filteredItsCameras.length === 0}
              >
                {filteredItsCameras.length === 0 && <option value="" disabled>카메라 없음</option>}
                {filteredItsCameras.map((cam, idx) => (
                  <option key={idx} value={cam.cctvurl}>{cam.cctvname}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="cctv-player-wrapper its-wrapper">
            {isLoadingIts ? (
              <div className="cctv-status-msg">
                <div className="spinner"></div>
                <p>ITS 데이터를 불러오는 중...</p>
              </div>
            ) : itsError ? (
              <div className="cctv-status-msg error">
                <i className="fa-solid fa-triangle-exclamation"></i>
                <p>{itsError}</p>
              </div>
            ) : selectedItsCam ? (
              <>
                <div className="player-container" style={{ width: '100%', height: '100%', position: 'relative' }}>
                  <ReactPlayer
                    key={selectedItsCam.cctvurl}
                    url={selectedItsCam.cctvurl}
                    playing={true}
                    controls={true}
                    muted={true}
                    width="100%"
                    height="100%"
                    className="react-player-instance"
                    config={{
                      file: {
                        forceHLS: true,
                        attributes: {
                          playsInline: true, // 대문자 I 확인!
                          controlsList: 'nodownload'
                        },
                        hlsOptions: {
                          enableWorker: true,
                          xhrSetup: function (xhr) {
                            xhr.withCredentials = false;
                          }
                        }
                      }
                    }}
                    onError={(e) => {
                      console.error("ITS Player Error:", e);
                    }}
                  />
                </div>
                <div className="cctv-overlay-info its-info">
                  {selectedItsCam.cctvname}
                </div>
              </>
            ) : (
              <div className="cctv-status-msg">
                <p>선택된 카메라가 없습니다.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CctvDashboard;