let map;
let marker;
let geocoder;
let autocomplete;

// 서울 시청 초기 좌표 (사용자가 위치를 변경했는지 확인하기 위한 용도)
const INITIAL_LAT = 37.5665;
const INITIAL_LNG = 126.9780;

// [설정 상수로 관리]
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const MAX_VIDEO_DURATION = 30; // 30초 제한
const ALLOWED_TYPES = [
    'image/jpeg', 'image/png', 'image/webp', 
    'video/mp4', 'video/quicktime', 'video/x-msvideo'
];

// [새로 추가] GPS 도분초 좌표를 실수형(Decimal)으로 변환
function convertToDecimal(gpsArray, ref) {
    if (!gpsArray) return null;
    let decimal = gpsArray[0] + (gpsArray[1] / 60) + (gpsArray[2] / 3600);
    if (ref === "S" || ref === "W") decimal = decimal * -1;
    return decimal;
}

// 1. 구글 지도 및 검색(Autocomplete) 초기화
function initMap() {
    const initialPos = { lat: INITIAL_LAT, lng: INITIAL_LNG }; 
    geocoder = new google.maps.Geocoder();
    
    map = new google.maps.Map(document.getElementById("map"), {
        center: initialPos,
        zoom: 15,
    });

    marker = new google.maps.Marker({
        position: initialPos,
        map: map,
        draggable: true,
    });

    initAutocomplete();

    google.maps.event.addListener(marker, 'dragend', function() {
        updatePosition(marker.getPosition());
    });

    map.addListener("click", (e) => {
        marker.setPosition(e.latLng);
        updatePosition(e.latLng);
    });
}

// 2. 주소 검색(자동완성) 기능
function initAutocomplete() {
    const input = document.getElementById("location_text");
    autocomplete = new google.maps.places.Autocomplete(input);
    
    autocomplete.addListener("place_changed", () => {
        const place = autocomplete.getPlace();
        if (!place.geometry || !place.geometry.location) return;

        map.setCenter(place.geometry.location);
        map.setZoom(17);
        marker.setPosition(place.geometry.location);
        
        document.getElementById("latitude").value = place.geometry.location.lat();
        document.getElementById("longitude").value = place.geometry.location.lng();
    });
}

// 3. 좌표 및 주소 텍스트 업데이트
function updatePosition(latLng) {
    if (!latLng) return;

    document.getElementById("latitude").value = latLng.lat();
    document.getElementById("longitude").value = latLng.lng();

    geocoder.geocode({ location: latLng }, (results, status) => {
        if (status === "OK" && results && results[0]) {
            document.getElementById("location_text").value = results[0].formatted_address;
        } else {
            console.error("주소 변환 실패:", status);
            document.getElementById("location_text").value = "주소를 불러오지 못했습니다.";
        }
    });
}

// 4. 모달 제어
function openMapModal() {
    document.getElementById("mapModal").style.display = "flex";
    setTimeout(() => {
        google.maps.event.trigger(map, "resize");
        if (marker) map.setCenter(marker.getPosition());
    }, 100);
}

function closeMapModal() {
    document.getElementById("mapModal").style.display = "none";
}

function confirmLocation() {
    if (!marker) {
        alert("위치를 먼저 선택하세요.");
        return;
    }

    const position = marker.getPosition();
    updatePosition(position);   // 현재 마커 위치를 주소/좌표로 다시 반영
    closeMapModal();
}

// 5. 내 현재 위치 찾기
function getCurrentLocation() {
    if (!navigator.geolocation) {
        alert("이 브라우저에서는 현재 위치 기능을 지원하지 않습니다.");
        return;
    }

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const pos = {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            };

            map.setCenter(pos);
            map.setZoom(17);
            marker.setPosition(pos);
            updatePosition(new google.maps.LatLng(pos.lat, pos.lng));
        },
        (error) => {
            console.error("현재 위치 가져오기 실패:", error);

            let message = "현재 위치를 가져올 수 없습니다.";
            if (error.code === 1) {
                message = "위치 권한이 차단되었습니다. 브라우저에서 위치 권한을 허용해주세요.";
            } else if (error.code === 2) {
                message = "현재 위치를 확인할 수 없습니다.";
            } else if (error.code === 3) {
                message = "위치 요청 시간이 초과되었습니다.";
            }

            alert(message);
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
        }
    );
}

// ---------------------------------------------------------
// 6. 파일 업로드 및 검증 로직 (30초 & 50MB 제한 적용)
// ---------------------------------------------------------
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('fileInput');

if (dropZone) {
    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.style.borderColor = '#FF6B00'; });
    dropZone.addEventListener('dragleave', () => { dropZone.style.borderColor = '#2A2A2A'; });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#2A2A2A';
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            handleFiles(e.dataTransfer.files[0]);
        }
    });
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFiles(e.target.files[0]);
    });
}

function handleFiles(file) {
    // 1. 형식 체크
    if (!ALLOWED_TYPES.includes(file.type)) {
        alert('이미지(jpg, png, webp) 또는 영상(mp4, mov) 파일만 가능합니다.');
        fileInput.value = '';
        return;
    }

    // 2. 용량 체크
    if (file.size > MAX_FILE_SIZE) {
        alert('파일 용량은 50MB를 넘을 수 없습니다.');
        fileInput.value = '';
        resetPreview();
        return;
    }

    // 📸 [1단계] 사진 EXIF GPS 추출 로직
    if (file.type === "image/jpeg" || file.type === "image/jpg") {
        EXIF.getData(file, function() {
            const lat = EXIF.getTag(this, "GPSLatitude");
            const lon = EXIF.getTag(this, "GPSLongitude");
            
            if (lat && lon) {
                const dLat = convertToDecimal(lat, EXIF.getTag(this, "GPSLatitudeRef"));
                const dLon = convertToDecimal(lon, EXIF.getTag(this, "GPSLongitudeRef"));
                
                // 위치 값은 무조건 저장
                if (map && marker) {
                    const latLng = new google.maps.LatLng(dLat, dLon);
                    marker.setPosition(latLng);
                    map.setCenter(latLng);
                    updatePosition(latLng);
                } else {
                    document.getElementById("latitude").value = dLat;
                    document.getElementById("longitude").value = dLon;
                }
                alert("사진의 위치 정보를 확인하여 자동 설정했습니다.");
            } else {
                getCurrentLocation(); 
            }
        });
    } else if (file.type.startsWith('video/')) {
        getCurrentLocation();
    }

    // --- 여기서부터 미리보기 생성 로직 (함수 안으로 들어와야 함) ---
    const previewContainer = document.getElementById('file-preview');
    // dropZone 존재 여부를 먼저 확인하여 에러 방지
    const infoText = dropZone ? dropZone.querySelector('p') : null;
    const icon = dropZone ? dropZone.querySelector('i') : null;
    const isVideo = file.type.startsWith('video/');

    const reader = new FileReader();
    
    reader.onload = (e) => {
        const fileSrc = e.target.result;

        if (isVideo) {
            const videoEl = document.createElement('video');
            videoEl.src = fileSrc;
            videoEl.preload = 'metadata';

            videoEl.addEventListener('loadedmetadata', function() {
                if (videoEl.duration > MAX_VIDEO_DURATION) {
                    alert(`영상 길이는 30초 이하만 가능합니다.`);
                    fileInput.value = ''; resetPreview(); return;
                }
                videoEl.controls = true;
                videoEl.autoplay = true;
                videoEl.muted = true;
                videoEl.classList.add('inner-preview');

                previewContainer.innerHTML = ''; 
                previewContainer.appendChild(videoEl);
                previewContainer.style.display = 'flex';
                
                if (infoText) infoText.style.display = 'none';
                if (icon) icon.style.display = 'none';
            });
        } else {
            const imgEl = document.createElement('img');
            imgEl.src = fileSrc;
            imgEl.classList.add('inner-preview');

            previewContainer.innerHTML = ''; 
            previewContainer.appendChild(imgEl);
            previewContainer.style.display = 'flex';
            
            if (infoText) infoText.style.display = 'none';
            if (icon) icon.style.display = 'none';
        }
    };
    
    reader.readAsDataURL(file);
} // <--- handleFiles 함수의 진짜 끝 지점!

// ---------------------------------------------------------
// 7. 신고 제출 로직 (트럭 주행 + 랜덤 장애물 )
// ---------------------------------------------------------
const reportForm = document.getElementById('reportForm');

if (reportForm) {
    reportForm.addEventListener('submit', async (e) => {
        e.preventDefault(); 

        // 🚨 [추가 포인트] 위치 정보가 없으면 차단
        const locationText = document.getElementById('location_text').value.trim();
        const lat = document.getElementById('latitude').value;

        // 주소가 비었거나, 좌표가 0이거나, 초기값(서울시청)이면 전송 중단
        if (!locationText || !lat || parseFloat(lat) === INITIAL_LAT) {
            alert("⚠️ 위치 정보가 반드시 필요합니다.\n사진을 올리거나 지도에서 정확한 위치를 선택해 주세요.");
            openMapModal(); // 지도 모달을 자동으로 열어줍니다.
            return; 
        }
        
        const modal = document.getElementById('loadingModal');
        const gaugeBar = document.getElementById('gaugeBar');
        const carIcon = document.getElementById('carIcon');
        const progressText = document.getElementById('progressText');
        const trashIcon = document.getElementById('trashIcon');
        const statusText = document.getElementById('loadingStatus'); 
        const obstacleImg = trashIcon ? trashIcon.querySelector('img') : null;

        // 1. 문구 배열
        const loadingPhrases = [
            "탐지 레이더 가동 중...",
            "도로 위 타이어 조각 찾는 중...",
            "낙석 위험 지형 분석 중...",
            "쓰레기 봉투 위치 파악 완료!",
            "AI가 먼지를 털어내고 있습니다...",
            "분석 결과 보고서 작성 중...",
            "깨끗한 도로를 시뮬레이션 중...",
            "거의 다 왔습니다! 엔진 예열 중..."
        ];

        // 2. 랜덤 장애물 설정
        const obstacles = ['trash.png', 'tire.png', 'rock.png'];
        const randomIndex = Math.floor(Math.random() * obstacles.length);
        const selectedImg = obstacles[randomIndex];
        
        if (obstacleImg) {
            obstacleImg.src = '/static/images/' + selectedImg;
            obstacleImg.style.display = 'block';
            obstacleImg.style.zIndex = '9999';
            if (trashIcon) trashIcon.classList.remove('hidden'); 
        }

        if (modal) modal.style.display = 'flex';

        // 3. 애니메이션 변수 설정 (에러 해결 핵심 위치)
        let progress = 0; 

        // UI 업데이트 내부 함수 (리스너 안에서 정의)
        const updateLoadingUI = (val) => {
            const currentVal = Math.floor(val);
            if (gaugeBar) gaugeBar.style.width = currentVal + '%';
            if (carIcon) carIcon.style.left = `calc(${currentVal}% - 15px)`;
            if (progressText) progressText.innerText = currentVal + '%';

            if (currentVal >= 50) {
                if (trashIcon && !trashIcon.classList.contains('hidden')) {
                    trashIcon.classList.add('hidden');
                }
            }
        };

        const animationInterval = setInterval(() => {
            if (progress < 90) {
                progress += Math.floor(Math.random() * 3) + 1;
                
                if (Math.floor(progress) % 15 === 0) { 
                    const phraseIndex = Math.floor(Math.random() * loadingPhrases.length);
                    if (statusText) statusText.innerText = loadingPhrases[phraseIndex];
                }
            } else if (progress < 98) {
                progress += 0.3;
                if (statusText) statusText.innerText = "마무리 작업 중...";
            }
            updateLoadingUI(progress);
        }, 200);

        // 4. 서버 전송 로직
        const formData = new FormData(reportForm);
        try {
            const response = await fetch(reportForm.action, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                clearInterval(animationInterval);
                updateLoadingUI(100);
                if (statusText) statusText.innerText = "분석 완료!";
                
                setTimeout(() => {
                    alert('신고가 성공적으로 접수되었습니다!');
                    window.location.href = '/reports/my-page';
                }, 500);
            } else {
                if (modal) modal.style.display = 'none';
                clearInterval(animationInterval);
                const result = await response.json();
                alert(result.message || '전송 오류');
            }
        } catch (error) {
            if (modal) modal.style.display = 'none';
            clearInterval(animationInterval);
            alert('통신 오류');
        }
    });
}