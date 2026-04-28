document.addEventListener("DOMContentLoaded", function () {
    /* ===== 1. 기본 요소 선언 ===== */
    const previewBox = document.getElementById("edit-file-preview");
    const fileInput = document.getElementById("new_file");
    const fileNameText = document.getElementById("edit-file-name");
    const deleteFileBtn = document.getElementById("delete-existing-file-btn");
    const deleteFileInput = document.getElementById("delete_file"); // hidden input
    const uploadBtn = document.querySelector(".edit-file-upload-btn");
    const editForm = document.querySelector(".edit-form") || document.querySelector("form");
    const loadingModal = document.getElementById("loadingModal");
    let loadingIntervalId = null;

    if (!previewBox) return;

    /* ===== 2.5 신고하기 페이지와 동일한 로딩 게이지 애니메이션 ===== */
    function startLoadingAnimation() {
        // 중복 실행 방지
        if (loadingIntervalId) return;

        const gaugeBar = document.getElementById('gaugeBar');
        const carIcon = document.getElementById('carIcon');
        const progressText = document.getElementById('progressText');
        const trashIcon = document.getElementById('trashIcon');
        const statusText = document.getElementById('loadingStatus');
        const obstacleImg = document.getElementById('randomObstacle') || (trashIcon ? trashIcon.querySelector('img') : null);

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

        const obstacles = ['trash.png', 'tire.png', 'rock.png'];
        const selectedImg = obstacles[Math.floor(Math.random() * obstacles.length)];

        if (obstacleImg) {
            obstacleImg.src = '/static/images/' + selectedImg;
            obstacleImg.style.display = 'block';
            obstacleImg.style.zIndex = '9999';
        }
        if (trashIcon) trashIcon.classList.remove('hidden');

        let progress = 0;

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

        loadingIntervalId = setInterval(() => {
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
    }

    /* ===== 2. 공통 함수 ===== */
    function showEmptyMessage(message) {
        previewBox.innerHTML = `<p class="edit-empty-file">${message}</p>`;
    }

    function renderFilePreview(fileUrl, fileType) {
        if (!fileUrl) {
            showEmptyMessage("등록된 파일이 없습니다.");
            return;
        }

        if (fileType.includes("image") || fileType === "이미지") {
            previewBox.innerHTML = `
                <div class="edit-file-preview-item">
                    <img src="${fileUrl}" class="edit-image-file">
                </div>`;
        } else if (fileType.includes("video") || fileType === "영상") {
            previewBox.innerHTML = `
                <div class="edit-file-preview-item">
                    <video controls class="edit-video-preview">
                        <source src="${fileUrl}">
                        브라우저가 영상을 지원하지 않습니다.
                    </video>
                </div>`;
        } else {
            previewBox.innerHTML = `
                <div class="edit-file-preview-item">
                    <a href="${fileUrl}" target="_blank" class="edit-file-link">파일 보기</a>
                </div>`;
        }
    }

    /* ===== 3. 초기 실행: 기존 파일 렌더링 ===== */
    const previewItem = document.querySelector(".edit-file-preview-item");
    if (previewItem && previewItem.dataset.fileUrl) {
        renderFilePreview(previewItem.dataset.fileUrl, previewItem.dataset.fileType);
    }

    /* ===== 4. 기존 파일 삭제 로직 ===== */
    if (deleteFileBtn && deleteFileInput) {
        deleteFileBtn.addEventListener("click", function () {
            if (!confirm("기존 파일을 삭제하시겠습니까? (저장 시 반영됩니다)")) return;

            deleteFileInput.value = "Y";
            showEmptyMessage("기존 파일이 삭제되었습니다. 새 파일을 선택해주세요.");
            this.style.display = "none";

            if (fileInput) fileInput.value = "";
            if (fileNameText) fileNameText.textContent = "선택된 파일 없음";
        });
    }

    /* ===== 5. 새 파일 선택 및 검증 ===== */
    if (fileInput) {
        fileInput.addEventListener("change", function () {
            const file = this.files[0];
            if (!file) return;

            // 용량 체크 (50MB)
            if (file.size > 50 * 1024 * 1024) {
                alert("파일 용량이 너무 큽니다. 50MB 이하만 가능합니다.");
                this.value = "";
                return;
            }

            if (deleteFileInput) deleteFileInput.value = "N";
            const objectUrl = URL.createObjectURL(file);

            // 영상일 경우 길이 체크 (30초)
            if (file.type.startsWith("video")) {
                const video = document.createElement('video');
                video.preload = 'metadata';
                video.onloadedmetadata = function() {
                    if (video.duration > 30) {
                        alert(`영상 길이가 30초를 초과합니다. (현재: ${Math.round(video.duration)}초)`);
                        fileInput.value = "";
                        URL.revokeObjectURL(objectUrl);
                    } else {
                        if (fileNameText) fileNameText.textContent = file.name;
                        renderFilePreview(objectUrl, "영상");
                    }
                };
                video.src = objectUrl;
            } else {
                if (fileNameText) fileNameText.textContent = file.name;
                renderFilePreview(objectUrl, file.type);
            }
        });
    }

    /* ===== 6. 폼 제출 시 AI 분석 모달 가동 ===== */
    if (editForm && loadingModal) {
        editForm.addEventListener("submit", function (e) {
            const isFileSelected = fileInput && fileInput.files.length > 0;

            if (isFileSelected) {
                console.log("[DEBUG] 새 파일 발견, AI 재분석 로딩 시작");
                loadingModal.style.display = "flex";

                // 만약 애니메이션 시작 함수가 별도로 있다면 호출
                startLoadingAnimation();
            } else {
                console.log("[DEBUG] 파일 변경 없음, 일반 수정 진행");
            }
        });
    }

    /* ===== 7. 파일 업로드 버튼 연동 ===== */
    if (uploadBtn && fileInput) {
        uploadBtn.addEventListener("click", (e) => {
            e.preventDefault();
            fileInput.click();
        });
    }
});