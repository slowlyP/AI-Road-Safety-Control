window.MyReportsApi = {
  // 🔹 로딩 중 필터/버튼 잠금 처리
  setFilterLoadingState(isLoading) {
    const targets = [
      "filter-keyword",
      "filter-region",
      "filter-status",
      "filter-file-type",
      "filter-sort",
      "filter-search-btn",
      "filter-reset-btn"
    ];

    targets.forEach((id) => {
      const element = document.getElementById(id);
      if (!element) return;

      element.disabled = isLoading;

      if (isLoading) {
        element.classList.add("is-loading");
      } else {
        element.classList.remove("is-loading");
      }
    });
  },

  // 🔹 리스트 영역 로딩 표시
  showListLoading() {
    const reportList = document.getElementById("report-list");
    const emptyBox = document.getElementById("empty-box");
    const paginationBox = document.getElementById("pagination");

    if (reportList) {
      reportList.innerHTML = `
        <div class="report-loading-box">
          <div class="report-loading-spinner"></div>
          <p class="report-loading-text">신고 목록을 불러오는 중입니다...</p>
        </div>
      `;
    }

    if (emptyBox) {
      emptyBox.style.display = "none";
    }

    if (paginationBox) {
      paginationBox.innerHTML = "";
    }
  },

  // 🔹 대시보드 새로고침
  async refreshDashboard() {
    const state = window.MyReportsState;
    const filters = window.MyReportsFilters;

    filters.syncFiltersFromForm();
    await this.loadMyReports(state.currentPage, true);
  },

  // 🔹 내 신고 목록 / 통계 / 탐지기록 불러오기
  async loadMyReports(page = 1, silent = false) {
    const state = window.MyReportsState;
    const filters = window.MyReportsFilters;
    const render = window.MyReportsRender;
    const slider = window.MyReportsSlider;

    const reportList = document.getElementById("report-list");
    const emptyBox = document.getElementById("empty-box");
    const todayDetectTrack = document.getElementById("todayDetectTrack");
    const todayDetectEmpty = document.getElementById("today-detect-empty");
    const paginationBox = document.getElementById("pagination");

    try {
      // 🔹 로딩 시작
      this.setFilterLoadingState(true);

      if (!silent) {
        this.showListLoading();
      }

      // 🔹 현재 필터 기준 쿼리스트링 생성
      const queryString = filters.buildQueryString(page);

      const response = await fetch(`/reports/my?${queryString}`, {
        method: "GET",
        credentials: "include"
      });

      const contentType = response.headers.get("content-type") || "";
      let result = null;

      // 🔹 JSON 응답만 정상 처리
      if (contentType.includes("application/json")) {
        result = await response.json();
      } else {
        const text = await response.text();
        throw new Error(`JSON 응답이 아닙니다. 응답 일부: ${text.slice(0, 120)}`);
      }

      // 🔹 응답 실패 시 화면 초기화
      if (!response.ok) {
        if (!silent) {
          if (reportList) reportList.innerHTML = "";
          if (emptyBox) {
            emptyBox.style.display = "block";
            emptyBox.textContent = result.message || "신고 목록을 불러오지 못했습니다.";
          }

          if (todayDetectTrack) todayDetectTrack.innerHTML = "";
          if (todayDetectEmpty) {
            todayDetectEmpty.style.display = "block";
            todayDetectEmpty.textContent = result.message || "오늘 탐지 기록을 불러오지 못했습니다.";
          }

          if (paginationBox) paginationBox.innerHTML = "";
        }

        slider.stopTodayDetectAutoScroll();
        slider.resetTodayDetectSliderState();
        render.resetSummary();
        return;
      }

      // 🔹 신고 목록 데이터
      const reports = Array.isArray(result.data?.reports) ? result.data.reports : [];

      // 🔹 페이지네이션 정보
      const pagination = result.data?.pagination || {
        page: 1,
        total_pages: 1,
        has_prev: false,
        has_next: false,
        total_count: 0
      };

      // 🔹 상단 요약 카드 데이터
      const summary = result.data?.summary || null;

      // 🔹 오늘 탐지 기록 데이터
      const todayDetectItems = Array.isArray(result.data?.today_detect)
        ? result.data.today_detect
        : (Array.isArray(result.data?.today_detect?.items) ? result.data.today_detect.items : []);

      // 🔹 전체 내 신고 기준 지역 목록
      const availableRegions = Array.isArray(result.data?.available_regions)
        ? result.data.available_regions
        : [];

      // 🔹 현재 페이지 상태 저장
      state.currentPage = pagination.page || 1;

      // 🔹 화면 렌더링
      render.updateSummary(reports, pagination, summary);
      render.renderTodayDetect(todayDetectItems);
      render.renderReportList(reports, availableRegions);
      render.renderPagination(pagination);

    } catch (error) {
      console.error("내 신고 목록 로딩 오류:", error);

      // 🔹 통신 오류 시 화면 초기화
      if (!silent) {
        if (reportList) reportList.innerHTML = "";
        if (emptyBox) {
          emptyBox.style.display = "block";
          emptyBox.textContent = "서버와 통신 중 오류가 발생했습니다.";
        }

        if (todayDetectTrack) todayDetectTrack.innerHTML = "";
        if (todayDetectEmpty) {
          todayDetectEmpty.style.display = "block";
          todayDetectEmpty.textContent = "오늘 탐지 기록을 불러오지 못했습니다.";
        }

        if (paginationBox) paginationBox.innerHTML = "";
      }

      slider.stopTodayDetectAutoScroll();
      slider.resetTodayDetectSliderState();
      render.resetSummary();
    } finally {
      // 🔹 로딩 종료
      this.setFilterLoadingState(false);
    }
  }
};