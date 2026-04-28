window.MyReportsUtils = {
  // input 값 가져오기 (trim 포함)
  getInputValue(id) {
    const element = document.getElementById(id);
    return element ? element.value.trim() : "";
  },

  // input 값 설정
  setInputValue(id, value) {
    const element = document.getElementById(id);
    if (element) {
      element.value = value;
    }
  },

  // 상태 → CSS 클래스 변환
  getStatusClass(status) {
    if (status === "접수") return "badge-status-received";
    if (status === "확인중") return "badge-status-checking";
    if (status === "처리완료" || status === "처리 완료") return "badge-status-done";
    if (status === "오탐") return "badge-status-false";
    return "badge-location"; // 기본값
  },

  // 위험도 → 클래스 (색상용)
  getTodayRiskClass(riskLevel) {
    const risk = String(riskLevel || "").trim();

    if (risk === "긴급") return "danger";
    if (risk === "위험") return "warning";
    if (risk === "주의") return "caution";

    return "safe"; // 기본 안전
  },

  // 위험도 → 아이콘
  getTodayRiskIcon(riskLevel) {
    const risk = String(riskLevel || "").trim();

    if (risk === "긴급") return "🚨";
    if (risk === "위험") return "⚠";
    if (risk === "주의") return "⚡";

    return "✔"; // 안전
  },

  // 날짜 문자열에서 "시:분"만 추출
  extractTime(createdAt) {
    if (!createdAt) return "-";

    const parts = String(createdAt).split(" ");
    if (parts.length < 2) return String(createdAt);

    const timeParts = parts[1].split(":");
    if (timeParts.length >= 2) {
      return `${timeParts[0]}:${timeParts[1]}`;
    }

    return parts[1];
  },

  // XSS 방지용 HTML escape 처리
  escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  },

  // debounce (이벤트 과도 호출 방지)
  debounce(callback, delay = 150) {
    let timer = null;

    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        callback(...args);
      }, delay);
    };
  },

  // 페이지 번호 계산 (... 포함 페이징)
  getPageNumbers(currentPageValue, totalPages) {
    const pages = [];

    // 전체 페이지가 적으면 그대로 출력
    if (totalPages <= 10) {
      for (let i = 1; i <= totalPages; i += 1) {
        pages.push(i);
      }
      return pages;
    }

    // 앞쪽 페이지 영역
    if (currentPageValue <= 5) {
      pages.push(1, 2, 3, 4, 5, 6, 7, "...", totalPages);
      return pages;
    }

    // 뒤쪽 페이지 영역
    if (currentPageValue >= totalPages - 4) {
      pages.push(1, "...");
      for (let i = totalPages - 6; i <= totalPages; i += 1) {
        pages.push(i);
      }
      return pages;
    }

    // 중간 영역 (... 양쪽)
    pages.push(
      1,
      "...",
      currentPageValue - 2,
      currentPageValue - 1,
      currentPageValue,
      currentPageValue + 1,
      currentPageValue + 2,
      "...",
      totalPages
    );

    return pages;
  }
};