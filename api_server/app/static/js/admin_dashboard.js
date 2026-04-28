/**
 * 관리자 대시보드 전용 스크립트
 *
 * 현재 역할
 * 1. 페이지 로드 확인
 * 2. 주요 영역 존재 여부 확인
 * 3. 통계 카드 간단한 인터랙션
 * 4. 추후 차트/필터/비동기 데이터 연결을 위한 구조 준비
 */

document.addEventListener("DOMContentLoaded", () => {
  // 관리자 대시보드가 정상적으로 로드되었는지 확인
  console.log("[Admin Dashboard] 스크립트 로드 완료");

  // 초기화 함수 실행
  initAdminDashboard();
});

/**
 * 관리자 대시보드 초기화 함수
 *
 * 페이지가 열릴 때 필요한 기능들을 한곳에서 실행한다.
 */
function initAdminDashboard() {
  bindSummaryCardEvents();
  checkDashboardSections();
  formatEmptyStates();
}

/**
 * 통계 카드에 간단한 인터랙션을 부여한다.
 *
 * 현재는 hover 시 data 속성을 활용할 수 있도록 기본 구조만 잡아둔다.
 * 나중에는 클릭 시 상세 페이지 이동, 필터 적용 등의 기능으로 확장 가능하다.
 */
function bindSummaryCardEvents() {
  const summaryCards = document.querySelectorAll(".summary-card");

  if (!summaryCards.length) {
    console.warn("[Admin Dashboard] summary-card 요소를 찾지 못했습니다.");
    return;
  }

  summaryCards.forEach((card, index) => {
    // 마우스를 올렸을 때 현재 카드 인덱스를 확인
    card.addEventListener("mouseenter", () => {
      console.log(`[Admin Dashboard] 통계 카드 hover: ${index + 1}번 카드`);
    });

    // 클릭 시 추후 상세 기능 연결 가능
    card.addEventListener("click", () => {
      const labelElement = card.querySelector(".summary-card-label");
      const labelText = labelElement ? labelElement.textContent.trim() : "통계 카드";

      console.log(`[Admin Dashboard] ${labelText} 카드 클릭`);

      // 예시:
      // if (labelText === "전체 신고") {
      //   window.location.href = "/admin/reports";
      // }
    });
  });
}

/**
 * 대시보드 주요 섹션이 정상적으로 렌더링되었는지 확인한다.
 *
 * 확인 대상
 * - 최근 신고 목록 패널
 * - 권한 신청 목록 패널
 */
function checkDashboardSections() {
  const dashboardPanels = document.querySelectorAll(".dashboard-panel");
  const reportTable = document.querySelector(".admin-table");
  const requestList = document.querySelector(".request-list");

  if (!dashboardPanels.length) {
    console.warn("[Admin Dashboard] dashboard-panel 요소가 없습니다.");
  } else {
    console.log(`[Admin Dashboard] 패널 개수: ${dashboardPanels.length}`);
  }

  if (reportTable) {
    console.log("[Admin Dashboard] 최근 신고 목록 테이블 확인 완료");
  } else {
    console.warn("[Admin Dashboard] 최근 신고 목록 테이블이 없습니다.");
  }

  if (requestList) {
    console.log("[Admin Dashboard] 권한 신청 목록 확인 완료");
  } else {
    console.warn("[Admin Dashboard] 권한 신청 목록이 없습니다.");
  }
}

/**
 * 비어 있는 상태 UI를 보조적으로 처리한다.
 *
 * 현재는 콘솔 확인용이며,
 * 나중에는 아이콘 추가 / 버튼 추가 / 안내 문구 변경 등으로 확장 가능하다.
 */
function formatEmptyStates() {
  const emptyMessage = document.querySelector(".empty-message");
  const emptyBox = document.querySelector(".empty-box");

  if (emptyMessage) {
    console.log("[Admin Dashboard] 최근 신고 데이터 없음 상태 확인");
  }

  if (emptyBox) {
    console.log("[Admin Dashboard] 권한 신청 대기 없음 상태 확인");
  }
}

/**
 * 추후 대시보드 통계를 비동기로 갱신할 때 사용할 수 있는 예시 함수
 *
 * 현재는 사용하지 않지만,
 * 나중에 fetch API로 통계 데이터를 다시 불러올 때 사용할 수 있다.
 */
async function fetchDashboardStats() {
  try {
    // 예시 URL
    // const response = await fetch("/admin/api/dashboard-stats");
    // const data = await response.json();
    // updateSummaryCards(data);

    console.log("[Admin Dashboard] fetchDashboardStats 함수 준비 완료");
  } catch (error) {
    console.error("[Admin Dashboard] 통계 데이터 조회 실패:", error);
  }
}

/**
 * 통계 카드 숫자를 업데이트하는 예시 함수
 *
 * @param {Object} stats - 서버에서 전달받은 통계 데이터
 */
function updateSummaryCards(stats) {
  if (!stats) {
    console.warn("[Admin Dashboard] 업데이트할 통계 데이터가 없습니다.");
    return;
  }

  // 예시 구조
  // document.querySelector('[data-stat="total"]').textContent = stats.total_reports;
  // document.querySelector('[data-stat="completed"]').textContent = stats.completed_reports;
  // document.querySelector('[data-stat="pending"]').textContent = stats.pending_reports;
  // document.querySelector('[data-stat="false"]').textContent = stats.false_reports;

  console.log("[Admin Dashboard] 통계 카드 업데이트 함수 준비 완료", stats);
}