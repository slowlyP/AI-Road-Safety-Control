window.MyReportsState = {
  // 현재 페이지 & 페이지당 개수
  currentPage: 1,
  perPage: 5,

  // 자동 새로고침 / 슬라이드 시간(ms)
  AUTO_REFRESH_MS: 30000,
  DETECT_AUTO_SLIDE_MS: 3000,

  // 슬라이더 자동 재생 관련
  detectAutoSlideTimer: null,      // setInterval 저장용
  detectAutoScrollPaused: false,   // hover 시 일시정지 여부

  // 슬라이더 위치 상태
  detectCurrentIndex: 0,           // 현재 카드 인덱스
  detectStepWidth: 0,              // 한 칸 이동 거리 (카드+gap)
  detectOriginalCount: 0,          // 원본 카드 개수
  detectSingleSetWidth: 0,         // 카드 한 세트 전체 너비

  // 신고 리스트 필터 상태
  reportFilters: {
    keyword: "",        // 검색어
    region: "",         // 지역 필터
    status: "",         // 상태 (접수, 처리완료 등)
    file_type: "",      // 파일 유형 (이미지/영상)
    sort: "latest",     // 정렬 기준
    start_date: "",     // 시작 날짜
    end_date: ""        // 종료 날짜
  }
};