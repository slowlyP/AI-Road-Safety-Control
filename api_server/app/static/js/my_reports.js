document.addEventListener("DOMContentLoaded", async () => {
  // 전역 모듈 가져오기 (상태 / 필터 / 슬라이더 / API)
  const state = window.MyReportsState;
  const filters = window.MyReportsFilters;
  const slider = window.MyReportsSlider;
  const api = window.MyReportsApi;

  // 필터 관련 이벤트 연결
  filters.bindFilterEvents();

  // 상단 요약 카드 클릭 이벤트 연결
  filters.bindSummaryCardEvents();

  // 화면의 현재 필터값을 state에 동기화
  filters.syncFiltersFromForm();

  // 첫 진입 시 활성 카드 스타일 동기화
  filters.updateSummaryCardActiveState();

  // 오늘 탐지기록 슬라이더 버튼 / hover 이벤트 연결
  slider.bindTodayDetectControls();

  // 화면 크기 변경 시 슬라이더 재계산 이벤트 연결
  slider.bindResizeEvent();

  // 첫 화면 진입 시 1페이지 데이터 로딩
  await api.loadMyReports(1);

  // 일정 시간마다 대시보드 데이터 자동 새로고침
  setInterval(() => {
    api.refreshDashboard();
  }, state.AUTO_REFRESH_MS);
});