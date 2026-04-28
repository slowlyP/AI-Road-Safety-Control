(function () {
    const socketStatusEl = document.getElementById("socket-status");
    const toastContainerEl = document.getElementById("realtime-alert-toast-container");

    const unreadTbodyEl = document.getElementById("realtime-alert-unread-tbody");
    const markAllBtn = document.getElementById("mark-all-alerts-read-btn");

    const unreadBadgeEls = document.querySelectorAll(".realtime-alert-badge");
    const tabUnreadCountEl = document.getElementById("tab-unread-count");

    const tabButtons = document.querySelectorAll(".realtime-alert-tab");
    const tabPanels = document.querySelectorAll(".realtime-alert-tab-panel");

    const checkedAlertGroupsEl = document.getElementById("checked-alert-groups");
    const checkedAlertsJsonEl = document.getElementById("checked-alerts-json");

    const dangerSoundEl = document.getElementById("sound-danger");
    const emergencySoundEl = document.getElementById("sound-emergency");

    const isRealtimePage = !!unreadTbodyEl && !!checkedAlertGroupsEl;

    let checkedAlertsStore = [];

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function formatConfidence(value) {
        const num = Number(value ?? 0);
        return Number.isNaN(num) ? "0.00" : num.toFixed(2);
    }

    function updateUnreadBadge(count) {
        unreadBadgeEls.forEach((badge) => {
            if (!badge) return;

            if (count > 0) {
                badge.textContent = String(count);
                badge.style.display = "inline-flex";
            } else {
                badge.textContent = "0";
                badge.style.display = "none";
            }
        });

        if (tabUnreadCountEl) {
            tabUnreadCountEl.textContent = String(count || 0);
        }
    }

    function setSocketStatus(text, className = "") {
        if (!socketStatusEl) return;
        socketStatusEl.textContent = text;
        socketStatusEl.className = className;
    }

    function playAlertSound(level) {
        try {
            if (level === "긴급") {
                if (!emergencySoundEl) return;
                emergencySoundEl.currentTime = 0;
                emergencySoundEl.play().catch((err) => {
                    console.warn("[RealtimeAlert] 긴급 사운드 재생 실패:", err);
                });
                return;
            }

            if (level === "위험") {
                if (!dangerSoundEl) return;
                dangerSoundEl.currentTime = 0;
                dangerSoundEl.play().catch((err) => {
                    console.warn("[RealtimeAlert] 위험 사운드 재생 실패:", err);
                });
            }
        } catch (err) {
            console.warn("[RealtimeAlert] 알림 사운드 재생 예외:", err);
        }
    }

    function levelClass(level) {
        return level === "긴급" ? "emergency" : "danger";
    }

    function switchTab(tabName) {
        tabButtons.forEach((btn) => {
            btn.classList.toggle("active", btn.dataset.tab === tabName);
        });

        tabPanels.forEach((panel) => {
            panel.classList.toggle("active", panel.id === `tab-${tabName}`);
        });
    }

    function removeEmptyRow() {
        const row = document.getElementById("empty-row-unread");
        if (row && row.parentNode) {
            row.parentNode.removeChild(row);
        }
    }

    function ensureUnreadEmptyRow() {
        if (!unreadTbodyEl) return;

        const rows = Array.from(unreadTbodyEl.querySelectorAll("tr"));
        const hasDataRow = rows.some((tr) => !tr.id);
        const existingEmptyRow = document.getElementById("empty-row-unread");

        if (!hasDataRow && !existingEmptyRow) {
            const tr = document.createElement("tr");
            tr.id = "empty-row-unread";
            tr.innerHTML = `<td colspan="9">현재 확인 대기 알림이 없습니다.</td>`;
            unreadTbodyEl.appendChild(tr);
        }

        if (hasDataRow && existingEmptyRow) {
            existingEmptyRow.remove();
        }
    }

    function showToast(alertData) {
        if (!toastContainerEl) return;

        const level = alertData.alert_level || alertData.risk_level || "위험";
        const toast = document.createElement("div");
        toast.className = `realtime-alert-toast ${level === "긴급" ? "emergency" : "danger"}`;

        toast.innerHTML = `
            <div class="realtime-alert-toast-header">
                <span>[${escapeHtml(level)}] 실시간 위험 알림</span>
                <button type="button" class="realtime-alert-toast-close" aria-label="닫기">×</button>
            </div>
            <div class="realtime-alert-toast-body">
                <div class="realtime-alert-toast-message">
                    ${escapeHtml(alertData.message || "")}
                </div>
                <div class="realtime-alert-toast-meta">
                    <div><strong>신고 제목:</strong> ${escapeHtml(alertData.report_title || "-")}</div>
                    <div><strong>위치:</strong> ${escapeHtml(alertData.location_text || "-")}</div>
                    <div><strong>탐지 객체:</strong> ${escapeHtml(alertData.detected_label || "-")}</div>
                    <div><strong>발생 시각:</strong> ${escapeHtml(alertData.created_at || "-")}</div>
                </div>
                <div class="realtime-alert-toast-actions">
                    <a href="/admin/reports/${alertData.report_id}" class="realtime-alert-toast-link">
                        상세보기
                    </a>
                </div>
            </div>
        `;

        toastContainerEl.prepend(toast);

        requestAnimationFrame(() => {
            toast.classList.add("show");
        });

        const closeBtn = toast.querySelector(".realtime-alert-toast-close");
        if (closeBtn) {
            closeBtn.addEventListener("click", () => removeToast(toast));
        }

        setTimeout(() => {
            removeToast(toast);
        }, 5000);
    }

    function removeToast(toastEl) {
        if (!toastEl) return;

        toastEl.classList.remove("show");

        setTimeout(() => {
            if (toastEl.parentNode) {
                toastEl.parentNode.removeChild(toastEl);
            }
        }, 300);
    }

    function parseInitialCheckedAlerts() {
        if (!checkedAlertsJsonEl) return [];

        try {
            const parsed = JSON.parse(checkedAlertsJsonEl.textContent || "[]");
            return Array.isArray(parsed) ? parsed : [];
        } catch (err) {
            console.warn("[RealtimeAlert] 확인 완료 초기 데이터 파싱 실패:", err);
            return [];
        }
    }

    function getDateOnly(createdAtText) {
        return String(createdAtText || "").split(" ")[0] || "";
    }

    function getTodayText() {
        const now = new Date();
        const yyyy = now.getFullYear();
        const mm = String(now.getMonth() + 1).padStart(2, "0");
        const dd = String(now.getDate()).padStart(2, "0");
        return `${yyyy}-${mm}-${dd}`;
    }

    function getYesterdayText() {
        const date = new Date();
        date.setDate(date.getDate() - 1);
        const yyyy = date.getFullYear();
        const mm = String(date.getMonth() + 1).padStart(2, "0");
        const dd = String(date.getDate()).padStart(2, "0");
        return `${yyyy}-${mm}-${dd}`;
    }

    function getDateGroupLabel(createdAtText) {
        const dateOnly = getDateOnly(createdAtText);
        const today = getTodayText();
        const yesterday = getYesterdayText();

        if (dateOnly === today) return "오늘";
        if (dateOnly === yesterday) return "어제";
        return "이전 이력";
    }

    function sortCheckedAlertsDesc(alerts) {
        return [...alerts].sort((a, b) => {
            const aTime = new Date((a.created_at || "").replace(" ", "T")).getTime() || 0;
            const bTime = new Date((b.created_at || "").replace(" ", "T")).getTime() || 0;
            return bTime - aTime;
        });
    }

    function groupCheckedAlerts(alerts) {
        const groups = {
            "오늘": [],
            "어제": [],
            "이전 이력": []
        };

        sortCheckedAlertsDesc(alerts).forEach((alert) => {
            const label = getDateGroupLabel(alert.created_at);
            groups[label].push(alert);
        });

        return groups;
    }

    function buildCheckedAlertCardHtml(alert) {
        const level = alert.alert_level || alert.risk_level || "위험";
        const levelCls = levelClass(level);

        return `
            <article class="checked-alert-card">
                <div class="checked-alert-main">
                    <div class="checked-alert-title-row">
                        <span class="alert-level-badge ${levelCls}">${escapeHtml(level)}</span>
                        <div class="checked-alert-message">${escapeHtml(alert.message || "")}</div>
                    </div>

                    <div class="checked-alert-subtext">
                        <div><strong>신고 제목</strong> · ${escapeHtml(alert.report_title || "-")}</div>
                        <div><strong>위치</strong> · ${escapeHtml(alert.location_text || "-")}</div>
                    </div>

                    ${
                        alert.file_path
                            ? `
                            <div class="checked-alert-preview">
                                <div class="realtime-alert-preview-label">탐지 이미지</div>
                                <img
                                    src="${escapeHtml(alert.file_path)}"
                                    alt="탐지 이미지"
                                    class="checked-alert-preview-image"
                                >
                            </div>
                            `
                            : ""
                    }
                </div>

                <div class="checked-alert-meta">
                    <div><strong>탐지 객체</strong> · ${escapeHtml(alert.detected_label || "-")}</div>
                    <div><strong>신뢰도</strong> · ${formatConfidence(alert.confidence)}</div>
                </div>

                <div class="checked-alert-side">
                    <div><strong>발생 시각</strong> · ${escapeHtml(alert.created_at || "-")}</div>
                </div>

                <div class="checked-alert-actions">
                    <a href="/admin/reports/${alert.report_id}" class="realtime-alert-toast-link">상세보기</a>
                    <span class="read-complete-badge">확인 완료</span>
                </div>
            </article>
        `;
    }

    function buildGroupHtml(label, items) {
        const isCollapsed = label === "이전 이력";
        const itemsHtml = items.map(buildCheckedAlertCardHtml).join("");

        return `
            <section class="checked-alert-group ${isCollapsed ? "collapsed" : ""}" data-group-label="${label}">
                <button type="button" class="checked-alert-group-header" data-group-toggle="${label}">
                    <div class="checked-alert-group-left">
                        <div class="checked-alert-group-title">${label}</div>
                        <div class="checked-alert-group-count">${items.length}건</div>
                    </div>
                    <div class="checked-alert-group-arrow">⌄</div>
                </button>

                <div class="checked-alert-group-body">
                    <div class="checked-alert-list">
                        ${itemsHtml}
                    </div>
                </div>
            </section>
        `;
    }

    function renderCheckedAlertGroups() {
        if (!checkedAlertGroupsEl) return;

        if (!checkedAlertsStore.length) {
            checkedAlertGroupsEl.innerHTML = `
                <div class="checked-alert-empty">
                    확인 완료된 알림이 없습니다.
                </div>
            `;
            return;
        }

        const grouped = groupCheckedAlerts(checkedAlertsStore);
        const orderedLabels = ["오늘", "어제", "이전 이력"];

        const html = orderedLabels
            .filter((label) => grouped[label].length > 0)
            .map((label) => buildGroupHtml(label, grouped[label]))
            .join("");

        checkedAlertGroupsEl.innerHTML = html;
    }

    function toggleCheckedGroup(label) {
        if (!checkedAlertGroupsEl) return;

        const groupEl = checkedAlertGroupsEl.querySelector(
            `.checked-alert-group[data-group-label="${label}"]`
        );

        if (!groupEl) return;

        groupEl.classList.toggle("collapsed");
    }

    function buildUnreadMainRow(alertData) {
        const tr = document.createElement("tr");
        tr.className = "unread new-alert-highlight";
        tr.dataset.alertId = alertData.alert_id;
        tr.dataset.alertLevel = alertData.alert_level || alertData.risk_level || "위험";

        const level = alertData.alert_level || alertData.risk_level || "위험";
        const levelCls = levelClass(level);

        tr.innerHTML = `
            <td>
                <span class="alert-level-badge ${levelCls}">
                    ${escapeHtml(level)}
                </span>
            </td>
            <td>${escapeHtml(alertData.message || "")}</td>
            <td>${escapeHtml(alertData.report_title || "-")}</td>
            <td>${escapeHtml(alertData.location_text || "-")}</td>
            <td>${escapeHtml(alertData.detected_label || "-")}</td>
            <td>${formatConfidence(alertData.confidence)}</td>
            <td>${escapeHtml(alertData.created_at || "-")}</td>
            <td>
                <a href="/admin/reports/${alertData.report_id}" class="realtime-alert-toast-link">
                    상세보기
                </a>
            </td>
            <td>
                <button
                    type="button"
                    class="mark-read-btn btn-mark-read"
                    data-alert-id="${alertData.alert_id}"
                >
                    확인 완료
                </button>
            </td>
        `;

        setTimeout(() => {
            tr.classList.remove("new-alert-highlight");
        }, 2400);

        return tr;
    }

    function buildUnreadImageRow(alertData) {
        if (!alertData.file_path) return null;

        const tr = document.createElement("tr");
        tr.className = "unread new-alert-highlight";
        tr.dataset.alertImageRow = "true";
        tr.dataset.parentAlertId = alertData.alert_id;

        tr.innerHTML = `
            <td colspan="9">
                <div class="realtime-alert-preview-box">
                    <div class="realtime-alert-preview-label">탐지 이미지</div>
                    <img
                        src="${escapeHtml(alertData.file_path)}"
                        alt="탐지 이미지"
                        class="realtime-alert-preview-image"
                    >
                </div>
            </td>
        `;

        setTimeout(() => {
            tr.classList.remove("new-alert-highlight");
        }, 2400);

        return tr;
    }

    function prependUnreadRows(alertData) {
        if (!unreadTbodyEl) return;

        const exists = unreadTbodyEl.querySelector(`tr[data-alert-id="${alertData.alert_id}"]`);
        if (exists) return;

        removeEmptyRow();

        const mainRow = buildUnreadMainRow(alertData);
        const imageRow = buildUnreadImageRow(alertData);

        if (imageRow) {
            unreadTbodyEl.prepend(imageRow);
        }
        unreadTbodyEl.prepend(mainRow);

        ensureUnreadEmptyRow();

        const unreadPanel = document.getElementById("tab-unread");
        if (unreadPanel && unreadPanel.classList.contains("active")) {
            unreadPanel.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
        }
    }

    function extractRowData(mainRow) {
        if (!mainRow) return null;

        const cells = mainRow.querySelectorAll("td");
        const detailLink = mainRow.querySelector(".realtime-alert-toast-link");
        const levelText = mainRow.dataset.alertLevel || (cells[0]?.innerText?.trim() || "위험");

        return {
            alert_id: mainRow.dataset.alertId,
            alert_level: levelText,
            message: cells[1]?.innerText?.trim() || "",
            report_title: cells[2]?.innerText?.trim() || "",
            location_text: cells[3]?.innerText?.trim() || "",
            detected_label: cells[4]?.innerText?.trim() || "",
            confidence: cells[5]?.innerText?.trim() || "0.00",
            created_at: cells[6]?.innerText?.trim() || "-",
            report_id: detailLink ? detailLink.getAttribute("href").split("/").pop() : ""
        };
    }

    function extractImagePath(imageRow) {
        if (!imageRow) return "";
        const img = imageRow.querySelector("img");
        return img ? img.getAttribute("src") : "";
    }

    function moveRowsToCheckedGroup(alertId) {
        if (!unreadTbodyEl) return;

        const mainRow = unreadTbodyEl.querySelector(`tr[data-alert-id="${alertId}"]`);
        const imageRow = unreadTbodyEl.querySelector(`tr[data-parent-alert-id="${alertId}"]`);

        if (!mainRow) return;

        const alertData = extractRowData(mainRow);
        if (!alertData) return;

        alertData.file_path = extractImagePath(imageRow);
        alertData.is_read = true;

        mainRow.classList.add("row-fade-out");
        if (imageRow) {
            imageRow.classList.add("row-fade-out");
        }

        setTimeout(() => {
            if (mainRow.parentNode) mainRow.parentNode.removeChild(mainRow);
            if (imageRow && imageRow.parentNode) imageRow.parentNode.removeChild(imageRow);

            checkedAlertsStore.unshift(alertData);
            renderCheckedAlertGroups();

            ensureUnreadEmptyRow();
        }, 240);
    }

    function moveAllUnreadRowsToCheckedGroup() {
        if (!unreadTbodyEl) return;

        const mainRows = Array.from(unreadTbodyEl.querySelectorAll("tr[data-alert-id]"));

        if (!mainRows.length) {
            ensureUnreadEmptyRow();
            renderCheckedAlertGroups();
            return;
        }

        const payloads = mainRows.map((mainRow) => {
            const alertId = mainRow.dataset.alertId;
            const imageRow = unreadTbodyEl.querySelector(`tr[data-parent-alert-id="${alertId}"]`);
            const alertData = extractRowData(mainRow);

            if (alertData) {
                alertData.file_path = extractImagePath(imageRow);
                alertData.is_read = true;
            }

            return { mainRow, imageRow, alertData };
        });

        payloads.forEach(({ mainRow, imageRow }) => {
            if (mainRow) mainRow.classList.add("row-fade-out");
            if (imageRow) imageRow.classList.add("row-fade-out");
        });

        setTimeout(() => {
            payloads.forEach(({ mainRow, imageRow, alertData }) => {
                if (mainRow && mainRow.parentNode) mainRow.parentNode.removeChild(mainRow);
                if (imageRow && imageRow.parentNode) imageRow.parentNode.removeChild(imageRow);
                if (alertData) checkedAlertsStore.unshift(alertData);
            });

            renderCheckedAlertGroups();
            ensureUnreadEmptyRow();
        }, 240);
    }

    async function fetchUnreadCount() {
        try {
            const response = await fetch("/admin/realtime-alerts/unread-count", {
                method: "GET",
                credentials: "same-origin"
            });

            const data = await response.json();

            if (!response.ok || !data.success) return;

            updateUnreadBadge(data.unread_count || 0);
        } catch (err) {
            console.warn("[RealtimeAlert] 미확인 개수 조회 오류:", err);
        }
    }

    async function markAlertAsRead(alertId) {
        try {
            const response = await fetch(`/admin/realtime-alerts/${alertId}/read`, {
                method: "PATCH",
                credentials: "same-origin"
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                console.warn("[RealtimeAlert] 확인 완료 처리 실패:", data);
                return;
            }

            moveRowsToCheckedGroup(alertId);
            updateUnreadBadge(data.unread_count || 0);
        } catch (err) {
            console.warn("[RealtimeAlert] 확인 완료 처리 오류:", err);
        }
    }

    async function markAllAlertsAsRead() {
        try {
            const response = await fetch("/admin/realtime-alerts/read-all", {
                method: "PATCH",
                credentials: "same-origin"
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                console.warn("[RealtimeAlert] 전체 확인 완료 실패:", data);
                return;
            }

            moveAllUnreadRowsToCheckedGroup();
            updateUnreadBadge(data.unread_count || 0);
        } catch (err) {
            console.warn("[RealtimeAlert] 전체 확인 완료 오류:", err);
        }
    }

    const socket = io("/admin/realtime-alert");

    socket.on("connect", () => {
        setSocketStatus("연결됨", "connected");
    });

    socket.on("disconnect", () => {
        setSocketStatus("연결 끊김", "disconnected");
    });

    socket.on("connect_error", (err) => {
        setSocketStatus("연결 오류", "error");
        console.warn("[RealtimeAlert] socket connect error:", err);
    });

    socket.on("new_realtime_alert", (data) => {
        const level = data.alert_level || data.risk_level || "위험";

        showToast(data);
        playAlertSound(level);

        if (isRealtimePage) {
            prependUnreadRows(data);
            switchTab("unread");
        }

        fetchUnreadCount();
    });

    document.addEventListener("click", (event) => {
        const markReadBtn = event.target.closest(".btn-mark-read");
        if (markReadBtn) {
            const alertId = markReadBtn.dataset.alertId;
            if (alertId) {
                markAlertAsRead(alertId);
            }
        }

        const tabBtn = event.target.closest(".realtime-alert-tab");
        if (tabBtn) {
            const tabName = tabBtn.dataset.tab;
            if (tabName) {
                switchTab(tabName);
            }
        }

        const groupToggleBtn = event.target.closest("[data-group-toggle]");
        if (groupToggleBtn) {
            const label = groupToggleBtn.dataset.groupToggle;
            if (label) {
                toggleCheckedGroup(label);
            }
        }
    });

    if (markAllBtn) {
        markAllBtn.addEventListener("click", () => {
            markAllAlertsAsRead();
        });
    }

    checkedAlertsStore = parseInitialCheckedAlerts();
    renderCheckedAlertGroups();

    window.markAlertAsRead = markAlertAsRead;

    fetchUnreadCount();
    ensureUnreadEmptyRow();
})();
