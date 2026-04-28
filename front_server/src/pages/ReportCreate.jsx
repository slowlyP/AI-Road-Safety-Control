import React, { useState, useRef, useEffect } from 'react';
import '../styles/ReportCreate.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

const ReportCreate = () => {
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    latitude: '',
    longitude: '',
    location_text: ''
  });
  const [files, setFiles] = useState([]);
  const [previewUrls, setPreviewUrls] = useState([]);
  const [isMapModalOpen, setIsMapModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);

  const fileInputRef = useRef(null);
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markerInstance = useRef(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length === 0) return;

    setFiles(selectedFiles);
    
    // Create previews
    const newPreviewUrls = selectedFiles.map(file => URL.createObjectURL(file));
    setPreviewUrls(newPreviewUrls);

    // Mock EXIF data extraction (since real EXIF parsing requires a library like exif-js)
    // If we had GPS data from photo, we'd set it here.
  };

  const initMap = () => {
    if (!window.google) return;
    
    if (!mapInstance.current && mapRef.current) {
      const defaultPos = { lat: 37.5665, lng: 126.9780 }; // Seoul
      mapInstance.current = new window.google.maps.Map(mapRef.current, {
        center: defaultPos,
        zoom: 14,
        styles: [
          { elementType: "geometry", stylers: [{ color: "#242f3e" }] },
          { elementType: "labels.text.stroke", stylers: [{ color: "#242f3e" }] },
          { elementType: "labels.text.fill", stylers: [{ color: "#746855" }] }
        ]
      });

      markerInstance.current = new window.google.maps.Marker({
        position: defaultPos,
        map: mapInstance.current,
        draggable: true
      });

      // Update position on map click
      mapInstance.current.addListener('click', (e) => {
        markerInstance.current.setPosition(e.latLng);
      });
    }
  };

  useEffect(() => {
    if (isMapModalOpen) {
      // Need a small timeout to ensure DOM is ready for the map
      setTimeout(() => {
        if (!window.google) {
          const script = document.createElement('script');
          script.src = `https://maps.googleapis.com/maps/api/js?key=${import.meta.env.VITE_GOOGLE_MAPS_API_KEY}&libraries=places`;
          script.async = true;
          script.defer = true;
          script.onload = initMap;
          document.head.appendChild(script);
        } else {
          initMap();
        }
      }, 100);
    }
  }, [isMapModalOpen]);

  const handleConfirmLocation = () => {
    if (markerInstance.current) {
      const pos = markerInstance.current.getPosition();
      const lat = pos.lat();
      const lng = pos.lng();
      
      // Reverse geocoding (mocked or real)
      if (window.google) {
        const geocoder = new window.google.maps.Geocoder();
        geocoder.geocode({ location: { lat, lng } }, (results, status) => {
          if (status === "OK" && results[0]) {
            setFormData(prev => ({
              ...prev,
              latitude: lat,
              longitude: lng,
              location_text: results[0].formatted_address
            }));
          } else {
            setFormData(prev => ({
              ...prev,
              latitude: lat,
              longitude: lng,
              location_text: `위도: ${lat.toFixed(4)}, 경도: ${lng.toFixed(4)}`
            }));
          }
          setIsMapModalOpen(false);
        });
      }
    }
  };

  const handleGetCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((position) => {
        const pos = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        if (mapInstance.current && markerInstance.current) {
          mapInstance.current.setCenter(pos);
          markerInstance.current.setPosition(pos);
        }
      });
    } else {
      alert('Geolocation is not supported by this browser.');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (files.length === 0) {
      alert("⚠️ 첨부된 파일이 없습니다.");
      return;
    }
    
    if (!formData.latitude || !formData.longitude) {
      alert("⚠️ 위치 정보가 누락되었습니다.\n지도에서 사고 발생 지점을 선택해 주세요.");
      return;
    }

    setIsLoading(true);
    setLoadingProgress(0);

    // Mock progress bar
    const progressInterval = setInterval(() => {
      setLoadingProgress(prev => {
        if (prev >= 90) return 90;
        return prev + 10;
      });
    }, 500);

    try {
      const submitData = new FormData();
      submitData.append('title', formData.title);
      submitData.append('content', formData.content);
      submitData.append('latitude', formData.latitude);
      submitData.append('longitude', formData.longitude);
      submitData.append('location_text', formData.location_text);
      
      files.forEach(file => {
        submitData.append('files', file); // 'files' is the key expected by backend
      });

      // Need to attach credentials if logged in
      const response = await fetch(`${API_BASE_URL}/api/report`, {
        method: 'POST',
        // credentials: 'include', // Enable this if using session cookies
        body: submitData
      });

      const data = await response.json();
      
      clearInterval(progressInterval);
      setLoadingProgress(100);
      
      setTimeout(() => {
        setIsLoading(false);
        if (data.success || response.ok) {
          alert('신고가 접수되었습니다.');
          // Redirect or reset form
          window.location.href = '/realtime-monitor';
        } else {
          alert(`오류: ${data.message || '알 수 없는 오류'}`);
        }
      }, 1000);
      
    } catch (error) {
      clearInterval(progressInterval);
      setIsLoading(false);
      console.error("Submit error:", error);
      alert('신고 접수 중 서버 오류가 발생했습니다.');
    }
  };

  return (
    <div className="report-container">
      <header className="report-header">
        <span className="logo-badge">AI</span>
        <h2>도로 위험 신고</h2>
        <p>AI 기반 도로 위험 요소 신고 시스템</p>
      </header>

      <form onSubmit={handleSubmit} className="report-form">
        <section className="form-section">
          <h3>📷 사진 및 영상 첨부</h3>
          <div 
            className="upload-box" 
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="upload-icon">☁️</div>
            <p>파일을 여기로 끌어다 놓거나 클릭하세요</p>
            <p className="upload-subtext">(영상 길이 30초 이하)</p>
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              accept="image/*,video/*" 
              multiple 
              hidden 
            />
          </div>
          {previewUrls.length > 0 && (
            <div className="preview-container">
              {previewUrls.map((url, index) => (
                <div key={index} className="preview-item">
                  {files[index].type.startsWith('video/') ? (
                    <video src={url} className="preview-media" />
                  ) : (
                    <img src={url} alt="preview" className="preview-media" />
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="form-section">
          <h3>📍 발생 위치</h3>
          <div className="location-group">
            <input 
              type="text" 
              name="location_text"
              value={formData.location_text}
              placeholder="지도를 클릭하여 위치를 지정하세요" 
              readOnly 
              className="location-input"
            />
            <button 
              type="button" 
              className="btn-secondary" 
              onClick={() => setIsMapModalOpen(true)}
            >
              지도에서 선택하기
            </button>
          </div>
        </section>

        <section className="form-section">
          <h3>📝 신고 정보</h3>
          <div className="input-group">
            <label>제목</label>
            <input 
              type="text" 
              name="title" 
              value={formData.title}
              onChange={handleInputChange}
              placeholder="입력하지 않으면 AI가 자동으로 작성합니다" 
            />
          </div>
          <div className="input-group">
            <label>상세 내용</label>
            <textarea 
              name="content" 
              value={formData.content}
              onChange={handleInputChange}
              rows="4" 
              placeholder="상황을 상세히 적어주세요"
            ></textarea>
          </div>
        </section>

        <button type="submit" className="btn-primary" disabled={isLoading}>
          {isLoading ? '신고 처리중...' : '신고 제출하기'}
        </button>
      </form>

      {/* Map Modal */}
      {isMapModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h4>위치 선택</h4>
              <button className="close-modal" onClick={() => setIsMapModalOpen(false)}>&times;</button>
            </div>
            <div ref={mapRef} className="map-container"></div>
            <div className="modal-actions">
              <button type="button" className="btn-secondary" onClick={handleGetCurrentLocation}>
                내 현재 위치 찾기
              </button>
              <button type="button" className="btn-primary" onClick={handleConfirmLocation}>
                이 위치로 지정
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Loading Modal */}
      {isLoading && (
        <div className="loading-modal-overlay">
          <div className="loading-modal-content">
            <h3>AI ANALYSIS</h3>
            <p className="loading-desc">도로 위 위험 요소를 분석 중입니다...</p>
            <div className="progress-bar-container">
              <div className="progress-bar" style={{ width: `${loadingProgress}%` }}></div>
            </div>
            <p className="progress-text">{loadingProgress}%</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportCreate;
