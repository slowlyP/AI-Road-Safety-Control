document.addEventListener("DOMContentLoaded", () => {
  const analysisEl = document.getElementById("ai-analysis-data");
  if (!analysisEl) return;

  let aiAnalysis = [];
  try {
    aiAnalysis = JSON.parse(analysisEl.textContent || "[]");
  } catch (e) {
    aiAnalysis = [];
  }

  renderAiSummary(aiAnalysis);
  renderAiHistory(aiAnalysis);
  initMediaCanvas(aiAnalysis);
  initCompareAnalysisGauge();
});

function initCompareAnalysisGauge() {
  const form = document.getElementById("compareAnalysisForm");
  if (!form) return;

  const modal = document.getElementById("loadingModal");
  const gaugeBar = document.getElementById("gaugeBar");
  const carIcon = document.getElementById("carIcon");
  const progressText = document.getElementById("progressText");
  const trashIcon = document.getElementById("trashIcon");
  const statusText = document.getElementById("loadingStatus");
  const obstacleImg = document.getElementById("randomObstacle");

  const loadingPhrases = [
    "비교 대상 데이터 수집 중...",
    "유사 사고 케이스 검색 중...",
    "탐지 결과 정합성 검증 중...",
    "리스크 스코어 재계산 중...",
    "요약 보고서 생성 중...",
    "거의 다 됐습니다. 마무리 중..."
  ];

  const obstacles = ["trash.png", "tire.png", "rock.png"];

  const setVisible = (visible) => {
    if (!modal) return;
    modal.style.display = visible ? "flex" : "none";
    modal.setAttribute("aria-hidden", visible ? "false" : "true");
  };

  const updateLoadingUI = (val) => {
    const currentVal = Math.max(0, Math.min(100, Math.floor(val)));

    if (gaugeBar) {
      gaugeBar.style.width = `${currentVal}%`;
    }

    if (carIcon) {
      carIcon.style.left = `calc(${currentVal}% - 15px)`;
    }

    if (progressText) {
      progressText.innerText = `${currentVal}%`;
    }

    if (currentVal >= 50 && trashIcon && !trashIcon.classList.contains("hidden")) {
      trashIcon.classList.add("hidden");
    }
  };

  const showRandomObstacle = () => {
    if (!obstacleImg) return;
    const selectedImg = obstacles[Math.floor(Math.random() * obstacles.length)];
    obstacleImg.src = `/static/images/${selectedImg}`;
    obstacleImg.style.display = "block";
    obstacleImg.style.zIndex = "9999";

    if (trashIcon) {
      trashIcon.classList.remove("hidden");
    }
  };

  const startFakeAnimation = () => {
    let progress = 0;
    updateLoadingUI(progress);

    const interval = window.setInterval(() => {
      if (progress < 20) {
        progress += 1;
      } else if (progress < 45) {
        progress += 0.8;
      } else if (progress < 70) {
        progress += 0.5;
      } else if (progress < 88) {
        progress += 0.2;
      } else if (progress < 95) {
        progress += 0.05;
      }

      if (Math.floor(progress) % 15 === 0 && statusText) {
        const phraseIndex = Math.floor(Math.random() * loadingPhrases.length);
        statusText.innerText = loadingPhrases[phraseIndex];
      }

      updateLoadingUI(progress);
    }, 250);

    return interval;
  };

  const finishLoading = (compareRunId, animationInterval, pollInterval, message) => {
    window.clearInterval(animationInterval);
    window.clearInterval(pollInterval);

    updateLoadingUI(100);

    if (statusText) {
      statusText.innerText = message;
    }

    window.setTimeout(() => {
      window.location.href = `/admin/reports/compare/${compareRunId}`;
    }, 700);
  };

  const pollCompareStatus = (compareRunId, animationInterval) => {
    const pollInterval = window.setInterval(async () => {
      try {
        const response = await fetch(`/admin/reports/compare/${compareRunId}/status`, {
          method: "GET",
          credentials: "same-origin",
          headers: {
            "X-Requested-With": "XMLHttpRequest"
          }
        });

        let data = null;
        try {
          data = await response.json();
        } catch (jsonErr) {
          throw new Error("상태 조회 응답이 올바른 JSON이 아닙니다.");
        }

        if (!response.ok || !data.success) {
          throw new Error(data?.message || "상태 조회 실패");
        }

        const totalCount = Number(data.total_count || 0);
        const doneCount = Number(data.done_count || 0);
        const runStatus = data.run_status || "";
        const models = Array.isArray(data.models) ? data.models : [];

        if (totalCount === 0) {
          if (statusText) {
            statusText.innerText = "AI 모델 준비 중...";
          }
          return;
        }

        const percent = Math.floor((doneCount / totalCount) * 100);
        updateLoadingUI(percent);

        if (statusText) {
          let modelText = "";
          if (models.length > 0) {
            modelText = " / " + models
              .map(m => `${m.model_name}:${m.status}`)
              .join(", ");
          }
          statusText.innerText = `비교분석 진행 중... (${doneCount}/${totalCount})${modelText}`;
        }

        if (runStatus === "완료") {
          finishLoading(compareRunId, animationInterval, pollInterval, "비교분석 완료!");
          return;
        }

        if (runStatus === "부분완료") {
          finishLoading(compareRunId, animationInterval, pollInterval, "일부 모델 완료");
          return;
        }

        if (runStatus === "실패") {
          finishLoading(compareRunId, animationInterval, pollInterval, "비교분석이 종료되었습니다.");
        }

      } catch (err) {
        window.clearInterval(animationInterval);
        window.clearInterval(pollInterval);
        setVisible(false);
        form.dataset.running = "0";
        alert(err.message || "비교분석 상태 조회 중 오류가 발생했습니다.");
      }
    }, 1500);
  };

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (form.dataset.running === "1") return;
    form.dataset.running = "1";

    showRandomObstacle();
    setVisible(true);
    updateLoadingUI(0);

    if (statusText) {
      statusText.innerText = "비교분석을 시작합니다...";
    }

    const animationInterval = startFakeAnimation();

    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        credentials: "same-origin",
        headers: {
          "X-Requested-With": "XMLHttpRequest"
        }
      });

      let data = null;
      try {
        data = await response.json();
      } catch (jsonErr) {
        throw new Error("비교분석 실행 응답이 올바른 JSON이 아닙니다.");
      }

      if (!response.ok || !data.success || !data.compare_run_id) {
        throw new Error(data?.message || "비교분석 실행에 실패했습니다.");
      }

      pollCompareStatus(data.compare_run_id, animationInterval);

    } catch (err) {
      window.clearInterval(animationInterval);
      setVisible(false);
      form.dataset.running = "0";
      alert(err.message || "통신 오류로 비교분석을 실행할 수 없습니다.");
    }
  });
}

function renderAiSummary(aiAnalysis) {
  const summaryBox = document.getElementById("ai-summary-box");
  if (!summaryBox) return;

  if (!Array.isArray(aiAnalysis) || !aiAnalysis.length) {
    summaryBox.innerHTML = '<div class="empty-box">탐지 결과가 없습니다.</div>';
    return;
  }

  const counts = {};
  aiAnalysis.forEach(item => {
    const key = item.label_kor || item.detected_label || "기타";
    counts[key] = (counts[key] || 0) + 1;
  });

  summaryBox.innerHTML = Object.entries(counts)
    .map(([label, count]) => `
      <div class="summary-item">
        <span class="summary-label">${label}</span>
        <strong class="summary-count">${count}건</strong>
      </div>
    `)
    .join("");
}

function renderAiHistory(aiAnalysis) {
  const historyBox = document.getElementById("ai-history-box");
  if (!historyBox) return;

  if (!Array.isArray(aiAnalysis) || !aiAnalysis.length) {
    historyBox.innerHTML = '<div class="empty-box">분석 이력이 없습니다.</div>';
    return;
  }

  const sorted = [...aiAnalysis].sort((a, b) => {
    const t1 = a.time_sec ?? -1;
    const t2 = b.time_sec ?? -1;
    if (t1 !== t2) return t1 - t2;
    return (a.id || 0) - (b.id || 0);
  });

  historyBox.innerHTML = sorted.map(item => {
    const timeText = item.time_sec != null ? `${Number(item.time_sec).toFixed(2)}초` : "이미지";
    const confText = item.confidence != null ? `${(Number(item.confidence) * 100).toFixed(1)}%` : "-";

    return `
      <div class="history-item">
        <div class="history-main">
          <strong>${item.label_kor || item.detected_label || "알 수 없음"}</strong>
        </div>
        <div class="history-sub">
          시간: ${timeText} / 정확도: ${confText}
        </div>
      </div>
    `;
  }).join("");
}

function initMediaCanvas(aiAnalysis) {
  const wrappers = document.querySelectorAll(".media-wrapper");

  wrappers.forEach(wrapper => {
    const fileId = Number(wrapper.dataset.fileId);
    const canvas = wrapper.querySelector("canvas");
    const image = wrapper.querySelector("img");
    const video = wrapper.querySelector("video");

    if (!canvas) return;

    const detections = (Array.isArray(aiAnalysis) ? aiAnalysis : []).filter(
      item => Number(item.file_id) === fileId
    );

    if (image) {
      image.addEventListener("load", () => {
        syncCanvasSize(canvas, image);
        drawImageDetections(canvas, image, detections);
      });

      if (image.complete) {
        syncCanvasSize(canvas, image);
        drawImageDetections(canvas, image, detections);
      }
    }

    if (video) {
      const renderVideo = () => {
        syncCanvasSize(canvas, video);
        drawVideoDetections(canvas, video, detections);
      };

      video.addEventListener("loadedmetadata", renderVideo);
      video.addEventListener("loadeddata", renderVideo);
      video.addEventListener("timeupdate", renderVideo);
      video.addEventListener("seeked", renderVideo);
      video.addEventListener("pause", renderVideo);
      video.addEventListener("play", renderVideo);
      window.addEventListener("resize", renderVideo);
    }
  });
}

function syncCanvasSize(canvas, mediaEl) {
  const rect = mediaEl.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = rect.height;
}

function drawImageDetections(canvas, image, detections) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  detections.forEach(item => {
    drawBox(ctx, canvas, {
      bbox: item.bbox,
      label: item.label_kor || item.detected_label,
      confidence: item.confidence,
      sourceWidth: image.naturalWidth || canvas.width,
      sourceHeight: image.naturalHeight || canvas.height
    });
  });
}

function drawVideoDetections(canvas, video, detections) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const currentTime = video.currentTime || 0;

  const visible = detections.filter(item => {
    if (item.time_sec == null) return false;
    return Math.abs(item.time_sec - currentTime) <= 0.20;
  });

  visible.forEach(item => {
    drawBox(ctx, canvas, {
      bbox: item.bbox,
      label: item.label_kor || item.detected_label,
      confidence: item.confidence,
      sourceWidth: item.frame_width || video.videoWidth || canvas.width,
      sourceHeight: item.frame_height || video.videoHeight || canvas.height
    });
  });
}

function drawBox(ctx, canvas, { bbox, label, confidence, sourceWidth, sourceHeight }) {
  if (!bbox || bbox.length !== 4 || !sourceWidth || !sourceHeight) return;

  const scaleX = canvas.width / sourceWidth;
  const scaleY = canvas.height / sourceHeight;

  const x1 = bbox[0] * scaleX;
  const y1 = bbox[1] * scaleY;
  const x2 = bbox[2] * scaleX;
  const y2 = bbox[3] * scaleY;

  const boxW = x2 - x1;
  const boxH = y2 - y1;

  ctx.lineWidth = 2;
  ctx.strokeStyle = "#ff3b30";
  ctx.strokeRect(x1, y1, boxW, boxH);

  const confText = confidence != null ? ` ${(Number(confidence) * 100).toFixed(1)}%` : "";
  const text = `${label}${confText}`;

  ctx.font = "14px Arial";
  const textWidth = ctx.measureText(text).width;
  const textHeight = 20;

  ctx.fillStyle = "#ff3b30";
  ctx.fillRect(x1, Math.max(0, y1 - textHeight), textWidth + 12, textHeight);

  ctx.fillStyle = "#ffffff";
  ctx.fillText(text, x1 + 6, Math.max(14, y1 - 6));
}