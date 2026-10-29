/* HistVault — iOS Design System Frontend Controller */
document.addEventListener("DOMContentLoaded", () => {
    let currentPage = 0;
    const pageSize = 40;
    let currentFilterTab = "all"; // all | deleted | active
    let currentCategory = "all";
    let currentBrowser = "all";
    let searchDebounceTimeout = null;

    // DOM Elements
    const statTotal = document.getElementById("stat-total");
    const statDeleted = document.getElementById("stat-deleted");
    const statActive = document.getElementById("stat-active");
    const statVisits = document.getElementById("stat-visits");
    const statDomainsSub = document.getElementById("stat-domains-sub");

    const searchInput = document.getElementById("search-input");
    const searchClearBtn = document.getElementById("search-clear-btn");
    const segmentButtons = document.querySelectorAll(".ios-segmented-control .ios-segment");
    const categoryChips = document.querySelectorAll(".ios-chips-scroll .ios-chip");
    const browserPills = document.querySelectorAll(".browser-pills .ios-mini-pill");
    const historyList = document.getElementById("history-list");
    const resultsCount = document.getElementById("results-count");
    const btnSync = document.getElementById("btn-sync");
    const syncIcon = document.getElementById("sync-icon");
    const btnPrev = document.getElementById("btn-prev");
    const btnNext = document.getElementById("btn-next");
    const pageIndicator = document.getElementById("page-indicator");

    // Export Dropdown
    const btnExportToggle = document.getElementById("btn-export-toggle");
    const exportMenu = document.getElementById("export-menu");

    // Modal Sheet
    const sheetBackdrop = document.getElementById("sheet-backdrop");
    const btnCloseSheet = document.getElementById("btn-close-sheet");
    const topDomainsContent = document.getElementById("top-domains-content");
    const tabTopDomainsTrigger = document.getElementById("tab-top-domains-trigger");
    const tabDeletedTrigger = document.getElementById("tab-deleted-trigger");
    const tabHistoryTrigger = document.getElementById("tab-history-trigger");
    const tabSyncTrigger = document.getElementById("tab-sync-trigger");

    // Load Stats from Vault API
    async function loadStats() {
        try {
            const res = await fetch("/api/stats");
            const data = await res.json();
            statTotal.textContent = Number(data.total_urls || 0).toLocaleString();
            statDeleted.textContent = Number(data.deleted_preserved_urls || 0).toLocaleString();
            statActive.textContent = Number(data.active_urls || 0).toLocaleString();
            statVisits.textContent = Number(data.total_visits || 0).toLocaleString();
            statDomainsSub.textContent = `across ${Number(data.unique_domains || 0).toLocaleString()} domains`;
        } catch (e) {
            console.error("Failed to load statistics:", e);
        }
    }

    // Load History Records with filters
    async function loadHistory() {
        const query = searchInput.value.trim();
        const offset = currentPage * pageSize;

        let url = `/api/history?limit=${pageSize}&offset=${offset}`;
        if (query) url += `&q=${encodeURIComponent(query)}`;
        if (currentBrowser !== "all") url += `&browser=${encodeURIComponent(currentBrowser)}`;
        if (currentCategory !== "all") url += `&category=${encodeURIComponent(currentCategory)}`;

        if (currentFilterTab === "deleted") {
            url += "&deleted_only=true";
        } else if (currentFilterTab === "active") {
            url += "&active_only=true";
        }

        resultsCount.textContent = "Searching Vault...";

        try {
            const res = await fetch(url);
            const data = await res.json();
            renderList(data.entries, query);
            resultsCount.textContent = `${data.entries.length} items on page ${currentPage + 1}`;

            btnPrev.disabled = currentPage === 0;
            btnNext.disabled = data.entries.length < pageSize;
            pageIndicator.textContent = `Page ${currentPage + 1}`;
        } catch (e) {
            console.error("Failed to load history list:", e);
            historyList.innerHTML = `
                <li class="ios-list-empty" style="color: var(--ios-red);">
                    <span>⚠️ Error loading history from vault database.</span>
                </li>
            `;
        }
    }

    // Render Inset Grouped List
    function renderList(entries, query) {
        if (!entries || entries.length === 0) {
            historyList.innerHTML = `
                <li class="ios-list-empty">
                    <span style="font-size: 32px;">🔍</span>
                    <strong style="color: var(--ios-label);">No History Records Found</strong>
                    <span style="font-size: 13px;">Try searching for a different keyword or change your filter.</span>
                </li>
            `;
            return;
        }

        historyList.innerHTML = entries.map(e => {
            const isDel = e.is_deleted_from_browser;
            const badgeClass = isDel ? "badge-ios-deleted" : "badge-ios-active";
            const badgeText = isDel ? "🔴 PRESERVED" : "🟢 ACTIVE";
            const timeLabel = formatRelativeTime(e.last_visit_utc);

            const browserIconClass = getBrowserIconClass(e.browser_name);
            const browserEmoji = getBrowserEmoji(e.browser_name);

            const displayTitle = highlightMatch(escapeHtml(e.title || e.url), query);
            const displayUrl = escapeHtml(e.url);
            const displayDomain = highlightMatch(escapeHtml(e.domain), query);

            return `
                <li class="ios-list-row">
                    <div class="ios-row-icon ${browserIconClass}" title="${escapeHtml(e.browser_name)}">
                        ${browserEmoji}
                    </div>
                    <div class="ios-row-main">
                        <div class="ios-row-title-line">
                            <a href="${displayUrl}" target="_blank" rel="noopener noreferrer" class="ios-row-title">
                                ${displayTitle}
                            </a>
                        </div>
                        <div class="ios-row-meta">
                            <span class="ios-domain-tag">${displayDomain}</span>
                            <span class="ios-category-badge">${escapeHtml(e.category)}</span>
                            <span class="ios-visits-count">• ${e.visit_count} visit${e.visit_count > 1 ? 's' : ''}</span>
                        </div>
                    </div>
                    <div class="ios-row-right">
                        <span class="ios-status-badge ${badgeClass}" title="${isDel ? 'History was deleted in browser, permanently saved in Vault!' : 'Active in browser'}">
                            ${badgeText}
                        </span>
                        <span class="ios-time-label">${timeLabel}</span>
                    </div>
                    <a href="${displayUrl}" target="_blank" rel="noopener noreferrer" class="ios-disclosure-arrow" title="Open Link">›</a>
                </li>
            `;
        }).join("");
    }

    // Helper: Browser Icons & Classes
    function getBrowserIconClass(browser) {
        if (!browser) return "";
        const b = browser.toLowerCase();
        if (b.includes("chrome")) return "icon-chrome";
        if (b.includes("edge")) return "icon-edge";
        if (b.includes("firefox")) return "icon-firefox";
        if (b.includes("brave")) return "icon-brave";
        if (b.includes("opera")) return "icon-opera";
        return "";
    }

    function getBrowserEmoji(browser) {
        if (!browser) return "🌐";
        const b = browser.toLowerCase();
        if (b.includes("chrome")) return "🌐";
        if (b.includes("edge")) return "🧭";
        if (b.includes("firefox")) return "🦊";
        if (b.includes("brave")) return "🦁";
        if (b.includes("opera")) return "⭕";
        return "🌐";
    }

    // Helper: Time Formatter
    function formatRelativeTime(isoString) {
        if (!isoString) return "-";
        try {
            const date = new Date(isoString);
            const now = new Date();
            const diffSeconds = Math.floor((now - date) / 1000);

            if (diffSeconds < 60) return "Just now";
            if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`;
            if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)}h ago`;
            if (diffSeconds < 172800) return "Yesterday";

            return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
        } catch (e) {
            return isoString.substring(0, 10);
        }
    }

    // Helper: String Highlighting & Escaping
    function highlightMatch(text, query) {
        if (!query || !text) return text;
        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, "gi");
        return text.replace(regex, `<mark style="background: rgba(255, 214, 10, 0.35); color: #fff; padding: 0 2px; border-radius: 3px;">$1</mark>`);
    }

    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Live Search Handling with Instant Debounce
    searchInput.addEventListener("input", () => {
        const val = searchInput.value;
        searchClearBtn.style.display = val.length > 0 ? "flex" : "none";

        clearTimeout(searchDebounceTimeout);
        searchDebounceTimeout = setTimeout(() => {
            currentPage = 0;
            loadHistory();
        }, 200);
    });

    searchClearBtn.addEventListener("click", () => {
        searchInput.value = "";
        searchClearBtn.style.display = "none";
        searchInput.focus();
        currentPage = 0;
        loadHistory();
    });

    // iOS Segmented Control Tabs
    segmentButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            segmentButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentFilterTab = btn.dataset.filter;
            currentPage = 0;
            loadHistory();
        });
    });

    // Category Filter Chips
    categoryChips.forEach(chip => {
        chip.addEventListener("click", () => {
            categoryChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            currentCategory = chip.dataset.category;
            currentPage = 0;
            loadHistory();
        });
    });

    // Browser Mini-Pills
    browserPills.forEach(pill => {
        pill.addEventListener("click", () => {
            browserPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            currentBrowser = pill.dataset.browser;
            currentPage = 0;
            loadHistory();
        });
    });

    // Pagination
    btnPrev.addEventListener("click", () => {
        if (currentPage > 0) {
            currentPage--;
            loadHistory();
            window.scrollTo({ top: 0, behavior: "smooth" });
        }
    });

    btnNext.addEventListener("click", () => {
        currentPage++;
        loadHistory();
        window.scrollTo({ top: 0, behavior: "smooth" });
    });

    // Sync Button
    btnSync.addEventListener("click", triggerSync);
    tabSyncTrigger.addEventListener("click", triggerSync);

    async function triggerSync() {
        syncIcon.textContent = "⏳";
        btnSync.disabled = true;
        try {
            const res = await fetch("/api/sync", { method: "POST" });
            const data = await res.json();
            await loadStats();
            await loadHistory();
            alert(`HistVault Sync Complete!\n\n• New URLs Archived: ${data.new_urls}\n• Updated Records: ${data.updated_urls}\n• Deleted in Browser (Preserved): ${data.newly_detected_deleted}\n• Total in Vault: ${data.total_preserved_urls}`);
        } catch (e) {
            alert("Sync Failed: " + e);
        } finally {
            syncIcon.textContent = "🔄";
            btnSync.disabled = false;
        }
    }

    // Export Dropdown Toggle
    btnExportToggle.addEventListener("click", (e) => {
        e.stopPropagation();
        exportMenu.classList.toggle("show");
    });

    document.addEventListener("click", () => {
        exportMenu.classList.remove("show");
    });

    // Bottom Bar Navigation Handlers
    tabHistoryTrigger.addEventListener("click", () => {
        // Switch to all history
        segmentButtons.forEach(b => b.classList.remove("active"));
        document.querySelector(".ios-segment[data-filter='all']").classList.add("active");
        currentFilterTab = "all";
        currentPage = 0;
        loadHistory();
        window.scrollTo({ top: 0, behavior: "smooth" });
    });

    tabDeletedTrigger.addEventListener("click", () => {
        // Switch to deleted preserved only
        segmentButtons.forEach(b => b.classList.remove("active"));
        document.querySelector(".ios-segment[data-filter='deleted']").classList.add("active");
        currentFilterTab = "deleted";
        currentPage = 0;
        loadHistory();
        window.scrollTo({ top: 0, behavior: "smooth" });
    });

    tabTopDomainsTrigger.addEventListener("click", async () => {
        sheetBackdrop.style.display = "flex";
        try {
            const res = await fetch("/api/top-domains?limit=15");
            const domains = await res.json();
            topDomainsContent.innerHTML = `
                <ul class="ios-domain-list">
                    ${domains.map((d, idx) => `
                        <li class="ios-domain-item">
                            <div>
                                <span style="color: var(--ios-secondary-label); margin-right: 8px;">#${idx + 1}</span>
                                <span class="ios-domain-name">${escapeHtml(d.domain)}</span>
                            </div>
                            <div class="ios-domain-stat">
                                <strong>${Number(d.total_visits).toLocaleString()}</strong> visits (${d.entry_count} URLs)
                            </div>
                        </li>
                    `).join("")}
                </ul>
            `;
        } catch (e) {
            topDomainsContent.innerHTML = "<p>Failed to load domain stats.</p>";
        }
    });

    btnCloseSheet.addEventListener("click", () => {
        sheetBackdrop.style.display = "none";
    });

    sheetBackdrop.addEventListener("click", (e) => {
        if (e.target === sheetBackdrop) {
            sheetBackdrop.style.display = "none";
        }
    });

    // Initial Data Fetch
    loadStats();
    loadHistory();
});
