window.MyReportsSlider = {
  // 오늘 탐지기록 슬라이더 버튼 & 마우스 이벤트 바인딩
  bindTodayDetectControls() {
    const state = window.MyReportsState;
    const slider = document.getElementById("todayDetectSlider");
    const prevBtn = document.getElementById("detectPrevBtn");
    const nextBtn = document.getElementById("detectNextBtn");

    if (!slider) return;

    // 마우스 올리면 자동 슬라이드 일시정지
    slider.addEventListener("mouseenter", () => {
      state.detectAutoScrollPaused = true;
    });

    // 마우스 나가면 자동 슬라이드 재개
    slider.addEventListener("mouseleave", () => {
      state.detectAutoScrollPaused = false;
    });

    // 이전 버튼 클릭
    if (prevBtn) {
      prevBtn.addEventListener("click", () => {
        this.moveTodayDetectSlider("prev");
      });
    }

    // 다음 버튼 클릭
    if (nextBtn) {
      nextBtn.addEventListener("click", () => {
        this.moveTodayDetectSlider("next");
      });
    }
  },

  // 화면 리사이즈 시 슬라이더 재계산
  bindResizeEvent() {
    const utils = window.MyReportsUtils;

    window.addEventListener("resize", utils.debounce(() => {
      this.recalculateTodayDetectSlider();
    }, 150));
  },

  // 슬라이더 이동 (이전 / 다음)
  moveTodayDetectSlider(direction) {
    const state = window.MyReportsState;

    if (!state.detectOriginalCount || !state.detectStepWidth) return;

    // 이동 시 자동 슬라이드 잠시 멈춤
    state.detectAutoScrollPaused = true;

    // 이전 버튼
    if (direction === "prev") {
      state.detectCurrentIndex =
        (state.detectCurrentIndex - 1 + state.detectOriginalCount) % state.detectOriginalCount;
    }
    // 다음 버튼
    else {
      state.detectCurrentIndex =
        (state.detectCurrentIndex + 1) % state.detectOriginalCount;
    }

    // 현재 위치로 스크롤 이동
    this.scrollTodayDetectToCurrentIndex(true);

    // 잠시 후 자동 슬라이드 재개
    setTimeout(() => {
      state.detectAutoScrollPaused = false;
    }, 400);
  },

  // 슬라이더 크기 및 이동 단위 재계산
  recalculateTodayDetectSlider() {
    const state = window.MyReportsState;
    const todayDetectTrack = document.getElementById("todayDetectTrack");
    const todayDetectSlider = document.getElementById("todayDetectSlider");

    if (!todayDetectTrack || !todayDetectSlider) return;

    const cards = todayDetectTrack.querySelectorAll(".detect-slide-card");

    // 카드 없으면 초기화
    if (!cards.length || !state.detectOriginalCount) {
      this.resetTodayDetectSliderState();
      todayDetectSlider.scrollLeft = 0;
      return;
    }

    const firstCard = cards[0];
    const trackStyle = window.getComputedStyle(todayDetectTrack);
    const gap = parseFloat(trackStyle.columnGap || trackStyle.gap || "0") || 0;

    // 한 칸 이동 거리 계산 (카드 + 간격)
    state.detectStepWidth = firstCard.offsetWidth + gap;

    // 한 세트 전체 너비 계산
    state.detectSingleSetWidth =
      (firstCard.offsetWidth * state.detectOriginalCount) +
      (gap * (state.detectOriginalCount - 1));

    // 현재 인덱스 위치로 이동
    this.scrollTodayDetectToCurrentIndex(false);
  },

  // 현재 인덱스 위치로 슬라이더 이동
  scrollTodayDetectToCurrentIndex(smooth = true) {
    const state = window.MyReportsState;
    const todayDetectSlider = document.getElementById("todayDetectSlider");

    if (!todayDetectSlider || state.detectStepWidth === 0 || state.detectSingleSetWidth === 0) return;

    // 무한 슬라이드 기준 위치 계산
    const targetLeft = state.detectSingleSetWidth + (state.detectCurrentIndex * state.detectStepWidth);

    // 부드러운 이동 or 즉시 이동
    if (smooth) {
      todayDetectSlider.scrollTo({
        left: targetLeft,
        behavior: "smooth"
      });
    } else {
      todayDetectSlider.scrollLeft = targetLeft;
    }
  },

  // 자동 슬라이드 시작
  startTodayDetectAutoScroll() {
    const state = window.MyReportsState;

    // 카드 1개면 자동슬라이드 불필요
    if (state.detectOriginalCount <= 1) return;

    this.stopTodayDetectAutoScroll();

    // 일정 시간마다 다음으로 이동
    state.detectAutoSlideTimer = setInterval(() => {
      if (state.detectAutoScrollPaused) return;
      this.moveTodayDetectSlider("next");
    }, state.DETECT_AUTO_SLIDE_MS);
  },

  // 자동 슬라이드 중지
  stopTodayDetectAutoScroll() {
    const state = window.MyReportsState;

    if (state.detectAutoSlideTimer) {
      clearInterval(state.detectAutoSlideTimer);
      state.detectAutoSlideTimer = null;
    }
  },

  // 슬라이더 상태 초기화
  resetTodayDetectSliderState() {
    const state = window.MyReportsState;

    state.detectCurrentIndex = 0;
    state.detectStepWidth = 0;
    state.detectOriginalCount = 0;
    state.detectSingleSetWidth = 0;
    state.detectAutoScrollPaused = false;
  }
};