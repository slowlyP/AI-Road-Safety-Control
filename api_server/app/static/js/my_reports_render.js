window.MyReportsRender = {
  // 상단 요약 카드 숫자 렌더링
  updateSummary(reports, pagination, summary) {
    const totalEl = document.getElementById("total-count");
    const receivedEl = document.getElementById("count-received");
    const doneEl = document.getElementById("count-done");
    const falseEl = document.getElementById("count-false");
    const checkingEl = document.getElementById("count-checking");

    if (!totalEl || !receivedEl || !doneEl || !falseEl || !checkingEl) return;

    // 서버 summary 값이 있으면 무조건 그 값을 사용
    // → 상단 요약 숫자는 항상 전체 기준으로 유지
    if (summary) {
      totalEl.textContent = summary.total ?? 0;
      receivedEl.textContent = summary.received ?? 0;
      doneEl.textContent = summary.done ?? 0;
      falseEl.textContent = summary.false_count ?? 0;
      checkingEl.textContent = summary.checking ?? 0;
      return;
    }

    // summary가 없으면 전체 개수만 pagination 기준으로 표시
    // 상태별 카운트는 필터된 reports 기준으로 계산하지 않음
    totalEl.textContent = pagination?.total_count ?? 0;
    receivedEl.textContent = "0";
    doneEl.textContent = "0";
    falseEl.textContent = "0";
    checkingEl.textContent = "0";
  },

  // 상단 요약 숫자 초기화
  resetSummary() {
    const totalEl = document.getElementById("total-count");
    const receivedEl = document.getElementById("count-received");
    const doneEl = document.getElementById("count-done");
    const falseEl = document.getElementById("count-false");
    const checkingEl = document.getElementById("count-checking");

    if (totalEl) totalEl.textContent = "0";
    if (receivedEl) receivedEl.textContent = "0";
    if (doneEl) doneEl.textContent = "0";
    if (falseEl) falseEl.textContent = "0";
    if (checkingEl) checkingEl.textContent = "0";
  },

  // 신고 리스트 렌더링
  renderReportList(reports, availableRegions = []) {
    const reportList = document.getElementById("report-list");
    const emptyBox = document.getElementById("empty-box");

    if (!reportList || !emptyBox) return;

    // 서버가 내려준 전체 지역 목록으로 지역 select 옵션 채우기
    this.renderRegionOptions(availableRegions);

    // 결과 없으면 빈 상태 표시
    if (reports.length === 0) {
      reportList.innerHTML = "";
      emptyBox.style.display = "block";
      emptyBox.textContent = "조건에 맞는 신고 내역이 없습니다.";
      return;
    }

    emptyBox.style.display = "none";
    reportList.innerHTML = reports.map((report) => this.createReportCard(report)).join("");
  },

  // 오늘 탐지기록 렌더링
  renderTodayDetect(items) {
    const state = window.MyReportsState;
    const slider = window.MyReportsSlider;

    const todayDetectTrack = document.getElementById("todayDetectTrack");
    const todayDetectEmpty = document.getElementById("today-detect-empty");
    const todayDetectSlider = document.getElementById("todayDetectSlider");

    if (!todayDetectTrack || !todayDetectEmpty || !todayDetectSlider) return;

    // 이전 자동 슬라이드 초기화
    slider.stopTodayDetectAutoScroll();
    slider.resetTodayDetectSliderState();

    // 오늘 탐지기록 없으면 빈 상태 표시
    if (!items || items.length === 0) {
      todayDetectTrack.innerHTML = "";
      todayDetectEmpty.style.display = "block";
      todayDetectEmpty.textContent = "오늘 등록된 긴급/위험/주의 신고가 없습니다.";
      todayDetectSlider.scrollLeft = 0;
      return;
    }

    todayDetectEmpty.style.display = "none";

    // 무한 슬라이드처럼 보이게 3세트 렌더링
    const singleSetHtml = items.map((item) => this.createTodayDetectItem(item)).join("");
    todayDetectTrack.innerHTML = singleSetHtml + singleSetHtml + singleSetHtml;

    state.detectOriginalCount = items.length;
    state.detectCurrentIndex = 0;

    setTimeout(() => {
      slider.recalculateTodayDetectSlider();

      if (state.detectOriginalCount > 1) {
        state.detectAutoScrollPaused = false;
        slider.startTodayDetectAutoScroll();
      }
    }, 50);
  },

  // 페이지네이션 렌더링
  renderPagination(pagination) {
    const utils = window.MyReportsUtils;
    const paginationBox = document.getElementById("pagination");
    if (!paginationBox) return;

    paginationBox.innerHTML = "";

    const { page, total_pages, has_prev, has_next } = pagination;

    // 페이지가 1개면 페이지네이션 숨김
    if (!total_pages || total_pages < 2) return;

    let html = "";

    // 이전 버튼
    html += `
      <button
        class="page-btn nav-btn prev-btn"
        ${!has_prev ? "disabled" : ""}
        onclick="window.MyReportsApi.loadMyReports(${page - 1})"
      >
        이전
      </button>
    `;

    const pages = utils.getPageNumbers(page, total_pages);

    // 숫자 버튼 / ... 렌더링
    pages.forEach((item) => {
      if (item === "...") {
        html += `<span class="page-ellipsis">...</span>`;
      } else {
        html += `
          <button
            class="page-btn number-btn ${item === page ? "active" : ""}"
            onclick="window.MyReportsApi.loadMyReports(${item})"
          >
            ${item}
          </button>
        `;
      }
    });

    // 다음 버튼
    html += `
      <button
        class="page-btn nav-btn next-btn"
        ${!has_next ? "disabled" : ""}
        onclick="window.MyReportsApi.loadMyReports(${page + 1})"
      >
        다음
      </button>
    `;

    paginationBox.innerHTML = html;
  },

  // 지역 select 옵션 렌더링
  renderRegionOptions(availableRegions = []) {
    const utils = window.MyReportsUtils;
    const regionSelect = document.getElementById("filter-region");

    if (!regionSelect) return;

    // 현재 선택값 유지
    const currentValue = regionSelect.value;

    // 중복 제거 + 빈 값 제거
    const regions = Array.isArray(availableRegions)
      ? [...new Set(availableRegions.filter((region) => region))]
      : [];

    let html = `<option value="">지역 전체</option>`;

    // 지역 옵션 생성
    regions.forEach((region) => {
      const safeRegion = utils.escapeHtml(region);
      html += `<option value="${safeRegion}">${safeRegion}</option>`;
    });

    regionSelect.innerHTML = html;

    // 기존 선택값이 아직 존재하면 유지
    const hasCurrentValue = regions.includes(currentValue);
    regionSelect.value = hasCurrentValue ? currentValue : "";
  },

  // 오늘 탐지 카드 1개 생성
  createTodayDetectItem(item) {
    const utils = window.MyReportsUtils;

    const title = utils.escapeHtml(item.title || "-");
    const location = utils.escapeHtml(item.location_text || "위치 정보 없음");
    const time = utils.escapeHtml(utils.extractTime(item.created_at || "-"));
    const riskClass = utils.getTodayRiskClass(item.risk_level || item.status);
    const riskLabel = utils.escapeHtml(item.risk_level || item.status || "안전");
    const riskIcon = utils.getTodayRiskIcon(item.risk_level || item.status);

    return `
      <article class="detect-slide-card ${riskClass}">
        <div class="detect-card-top">
          <span class="detect-time">${time}</span>

          <span class="badge ${riskClass}">
            <span class="status-icon">${riskIcon}</span>
            ${riskLabel}
          </span>
        </div>

        <div class="detect-card-body">
          <p class="detect-title-text">${title}</p>
          <p class="detect-location">${location}</p>
        </div>
      </article>
    `;
  },

  // 신고 카드 1개 생성
  createReportCard(report) {
    const utils = window.MyReportsUtils;

    return `
      <article class="report-card">
        <div class="report-top">
          <h3 class="report-title">${utils.escapeHtml(report.title || "-")}</h3>
          <div class="report-date">${utils.escapeHtml(report.created_at || "-")}</div>
        </div>

        <div class="report-content">
          ${utils.escapeHtml(report.content || "내용이 없습니다.")}
        </div>

        <div class="report-meta-row">
          <div class="report-meta">
            <span class="meta-badge badge-type">${utils.escapeHtml(report.file_type || "일반")}</span>
            <span class="meta-badge badge-location">${utils.escapeHtml(report.location_text || "위치 정보 없음")}</span>
            <span class="meta-badge ${utils.getStatusClass(report.status)}">${utils.escapeHtml(report.status || "-")}</span>
          </div>

          <a href="/reports/${report.id}/page" class="detail-btn">상세보기</a>
        </div>
      </article>
    `;
  }
};