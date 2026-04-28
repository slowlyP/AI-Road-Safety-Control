// 페이지 로드 후 첨부파일 미리보기 렌더링
document.addEventListener("DOMContentLoaded", function () {
  const item = document.querySelector(".file-preview-item");
  const previewBox = document.getElementById("detail-image-preview");

  // 미리보기 대상 요소가 없으면 종료
  if (!item || !previewBox) return;

  const fileUrl = String(item.dataset.fileUrl || "").trim();
  const fileType = String(item.dataset.fileType || "").trim();

  // 파일 정보가 없으면 안내문 표시
  if (!fileUrl || !fileType) {
    previewBox.innerHTML = '<p class="image-empty-text">등록된 파일이 없습니다.</p>';
    return;
  }

  // 이미지 파일이면 img 태그 렌더링
  if (fileType === "이미지") {
    item.innerHTML = `
      <img src="${fileUrl}" alt="신고 이미지" id="preview-image" class="detail-image-file">
    `;
  }
  // 영상 파일이면 video 태그 렌더링
  else if (fileType === "영상") {
    item.innerHTML = `
      <video controls id="preview-video" class="detail-video-preview">
        <source src="${fileUrl}">
        브라우저가 영상을 지원하지 않습니다.
      </video>
    `;
  }
  // 그 외 파일이면 링크로 표시
  else {
    item.innerHTML = `
      <a href="${fileUrl}" target="_blank" class="file-download-link">파일 보기</a>
    `;
  }

  // 토스트 메시지 3초 후 자동 숨김
  const toastMessages = document.querySelectorAll(".toast-message");
  if (toastMessages.length > 0) {
    setTimeout(function () {
      toastMessages.forEach(function (msg) {
        msg.style.display = "none";
      });
    }, 3000);
  }
});