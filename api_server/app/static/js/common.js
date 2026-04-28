document.addEventListener("DOMContentLoaded", function () {
  const menuToggle = document.getElementById("menuToggle");
  const mainNav = document.getElementById("mainNav");
  const headerActions = document.querySelector(".header-actions");
  const header = document.getElementById("siteHeader");

  // 모바일 메뉴 토글
  if (menuToggle && mainNav && headerActions) {
    menuToggle.addEventListener("click", function () {
      mainNav.classList.toggle("active");
      headerActions.classList.toggle("active");
    });
  }

  // 스크롤 시 헤더 배경 변화
  window.addEventListener("scroll", function () {
    if (!header) return;

    if (window.scrollY > 20) {
      header.classList.add("scrolled");
    } else {
      header.classList.remove("scrolled");
    }
  });
});