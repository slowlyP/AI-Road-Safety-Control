window.MyReportsFilters = {
  // 필터 폼 이벤트 연결
  bindFilterEvents() {
    const state = window.MyReportsState;
    const api = window.MyReportsApi;

    const filterForm = document.getElementById("report-filter-form");
    const resetBtn = document.getElementById("filter-reset-btn");

    const keywordInput = document.getElementById("filter-keyword");
    const regionSelect = document.getElementById("filter-region");
    const statusSelect = document.getElementById("filter-status");
    const fileTypeSelect = document.getElementById("filter-file-type");
    const sortSelect = document.getElementById("filter-sort");

    // 검색 버튼 클릭 시 필터 적용
    if (filterForm) {
      filterForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        this.syncFiltersFromForm();
        this.updateSummaryCardActiveState();
        state.currentPage = 1;
        await api.loadMyReports(1);
      });
    }

    // 검색어 입력 후 Enter 시 바로 검색
    if (keywordInput) {
      keywordInput.addEventListener("keydown", async (event) => {
        if (event.key === "Enter") {
          event.preventDefault(); // form submit 중복 방지
          this.syncFiltersFromForm();
          this.updateSummaryCardActiveState();
          state.currentPage = 1;
          await api.loadMyReports(1);
        }
      });
    }

    // 지역 변경 시 즉시 필터 적용
    if (regionSelect) {
      regionSelect.addEventListener("change", async () => {
        this.syncFiltersFromForm();
        this.updateSummaryCardActiveState();
        state.currentPage = 1;
        await api.loadMyReports(1);
      });
    }

    // 상태 변경 시 즉시 필터 적용
    if (statusSelect) {
      statusSelect.addEventListener("change", async () => {
        this.syncFiltersFromForm();
        this.updateSummaryCardActiveState();
        state.currentPage = 1;
        await api.loadMyReports(1);
      });
    }

    // 파일 유형 변경 시 즉시 필터 적용
    if (fileTypeSelect) {
      fileTypeSelect.addEventListener("change", async () => {
        this.syncFiltersFromForm();
        this.updateSummaryCardActiveState();
        state.currentPage = 1;
        await api.loadMyReports(1);
      });
    }

    // 정렬 변경 시 즉시 필터 적용
    if (sortSelect) {
      sortSelect.addEventListener("change", async () => {
        this.syncFiltersFromForm();
        this.updateSummaryCardActiveState();
        state.currentPage = 1;
        await api.loadMyReports(1);
      });
    }

    // 초기화 버튼 클릭 시 전체 필터 초기화
    if (resetBtn) {
      resetBtn.addEventListener("click", async () => {
        this.resetFilterForm();
        this.syncFiltersFromForm();
        this.updateSummaryCardActiveState();
        state.currentPage = 1;
        await api.loadMyReports(1);
      });
    }
  },

  // 상단 요약 카드 클릭 이벤트 연결
  bindSummaryCardEvents() {
    const state = window.MyReportsState;
    const api = window.MyReportsApi;
    const cards = document.querySelectorAll(".summary-filter-card");
    const statusSelect = document.getElementById("filter-status");

    if (!cards.length) return;

    cards.forEach((card) => {
      card.addEventListener("click", async () => {
        const clickedStatus = card.dataset.status || "";

        // 같은 카드 다시 누르면 전체 해제
        if (state.reportFilters.status === clickedStatus) {
          state.reportFilters.status = "";
        } else {
          state.reportFilters.status = clickedStatus;
        }

        // 아래 상태 select 값도 같이 변경
        if (statusSelect) {
          statusSelect.value = state.reportFilters.status;
        }

        // 활성 카드 스타일 갱신
        this.updateSummaryCardActiveState();

        // 첫 페이지부터 다시 조회
        state.currentPage = 1;
        await api.loadMyReports(1);
      });
    });
  },

  // 현재 status 값 기준으로 상단 요약 카드 active 표시
  updateSummaryCardActiveState() {
    const state = window.MyReportsState;
    const cards = document.querySelectorAll(".summary-filter-card");
    const currentStatus = state.reportFilters.status || "";

    cards.forEach((card) => {
      const cardStatus = card.dataset.status || "";

      if (cardStatus === currentStatus) {
        card.classList.add("active");
      } else {
        card.classList.remove("active");
      }
    });
  },

  // 화면의 필터값을 state에 동기화
  syncFiltersFromForm() {
    const state = window.MyReportsState;
    const utils = window.MyReportsUtils;

    state.reportFilters.keyword = utils.getInputValue("filter-keyword");
    state.reportFilters.region = utils.getInputValue("filter-region");
    state.reportFilters.status = utils.getInputValue("filter-status");
    state.reportFilters.file_type = utils.getInputValue("filter-file-type");
    state.reportFilters.sort = utils.getInputValue("filter-sort") || "latest";
    state.reportFilters.start_date = utils.getInputValue("filter-start-date");
    state.reportFilters.end_date = utils.getInputValue("filter-end-date");
  },

  // 필터 입력값 전체 초기화
  resetFilterForm() {
    const utils = window.MyReportsUtils;

    utils.setInputValue("filter-keyword", "");
    utils.setInputValue("filter-region", "");
    utils.setInputValue("filter-status", "");
    utils.setInputValue("filter-file-type", "");
    utils.setInputValue("filter-sort", "latest");
    utils.setInputValue("filter-start-date", "");
    utils.setInputValue("filter-end-date", "");
  },

  // 현재 필터 상태를 query string으로 변환
  buildQueryString(page) {
    const state = window.MyReportsState;
    const params = new URLSearchParams();

    params.set("page", page);
    params.set("per_page", state.perPage);

    if (state.reportFilters.keyword) params.set("keyword", state.reportFilters.keyword);
    if (state.reportFilters.region) params.set("region", state.reportFilters.region);
    if (state.reportFilters.status) params.set("status", state.reportFilters.status);
    if (state.reportFilters.file_type) params.set("file_type", state.reportFilters.file_type);
    if (state.reportFilters.sort) params.set("sort", state.reportFilters.sort);
    if (state.reportFilters.start_date) params.set("start_date", state.reportFilters.start_date);
    if (state.reportFilters.end_date) params.set("end_date", state.reportFilters.end_date);

    return params.toString();
  }
};