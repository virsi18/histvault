/* Apple Native Dark History Controller */
document.addEventListener("DOMContentLoaded", () => {
    let currentPage = 0;
    const pageSize = 40;
    let currentFilterTab = "all"; // all | deleted | active
    let currentCategory = "all";
    let currentBrowser = "all";
    let searchDebounceTimeout = null;

    // Elements
    const metaCaption = document.getElementById("meta-caption");
    const statTotal = document.getElementById("stat-total");
    const statDeleted = document.getElementById("stat-deleted");
    const statActive = document.getElementById("stat-active");
    const statVisits = document.getElementById("stat-visits");

    const searchInput = document.getElementById("search-input");
    const searchClearBtn = document.getElementById("search-clear-btn");
    const segmentButtons = document.querySelectorAll(".segmented-control .segment-btn");
    const categoryChips = document.querySelectorAll(".filter-chips .chip");
    const browserDropdown = document.getElementById("browser-dropdown");
    const historyList = document.getElementById("history-list");
    const resultsCount = document.getElementById("results-count");
    const btnSync = document.getElementById("btn-sync");
    const syncSvg = document.getElementById("sync-svg");
    const btnPrev = document.getElementById("btn-prev");
    const btnNext = document.getElementById("btn-next");
    const pageIndicator = document.getElementById("page-indicator");

    const btnExportToggle = document.getElementById("btn-export-toggle");
    const exportMenu = document.getElementById("export-menu");

    // Shortcut: Cmd+K or Ctrl+K focuses search box
    document.addEventListener("keydown", (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
            e.preventDefault();
            searchInput.focus();
            searchInput.select();
        }
        if (e.key === "Escape" && document.activeElement === searchInput) {
            searchInput.blur();
        }
    });

    // Fetch Statistics
    async function loadStats() {
        try {
            const res = await fetch("/api/stats");
            const data = await res.json();
            const total = Number(data.total_urls || 0);
            const deleted = Number(data.deleted_preserved_urls || 0);
            const active = Number(data.active_urls || 0);
            const visits = Number(data.total_visits || 0);
            const domains = Number(data.unique_domains || 0);

            statTotal.textContent = total.toLocaleString();
            statDeleted.textContent = deleted.toLocaleString();
            statActive.textContent = active.toLocaleString();
            statVisits.textContent = visits.toLocaleString();

            metaCaption.textContent = `${total.toLocaleString()} records • ${deleted.toLocaleString()} preserved from deletion`;
        } catch (e) {
            console.error("Stats request error:", e);
        }
    }

    // Fetch and render history
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

        resultsCount.textContent = "Updating...";

        try {
            const res = await fetch(url);
            const data = await res.json();
            renderRows(data.entries, query);
            resultsCount.textContent = `${data.entries.length} items on page ${currentPage + 1}`;

            btnPrev.disabled = currentPage === 0;
            btnNext.disabled = data.entries.length < pageSize;
            pageIndicator.textContent = `${currentPage + 1}`;
        } catch (e) {
            console.error("History fetch error:", e);
            historyList.innerHTML = `
                <li class="list-placeholder" style="color: var(--system-red);">
                    <span>Unable to connect to local vault database.</span>
                </li>
            `;
        }
    }

    // Render list items
    function renderRows(entries, query) {
        if (!entries || entries.length === 0) {
            historyList.innerHTML = `
                <li class="list-placeholder">
                    <span style="font-weight: 500; color: var(--label-primary);">No records found</span>
                    <span style="font-size: 12px; color: var(--label-tertiary);">No entries match the current search or filter query.</span>
                </li>
            `;
            return;
        }

        historyList.innerHTML = entries.map(e => {
            const isDel = e.is_deleted_from_browser;
            const statusBadge = isDel
                ? `<span class="status-pill pill-preserved" title="Deleted in browser history, permanently retained in Vault">Preserved</span>`
                : `<span class="status-pill pill-active">Active</span>`;

            const domainLetter = getDomainInitial(e.domain);
            const timeFormatted = formatTime(e.last_visit_utc);

            const safeTitle = highlightText(escapeHtml(e.title || e.url), query);
            const safeUrl = escapeHtml(e.url);
            const safeDomain = highlightText(escapeHtml(e.domain), query);

            return `
                <li class="history-row">
                    <div class="domain-avatar">${domainLetter}</div>
                    <div class="row-content">
                        <div class="row-title-bar">
                            <a href="${safeUrl}" target="_blank" rel="noopener noreferrer" class="row-title">
                                ${safeTitle}
                            </a>
                        </div>
                        <div class="row-subtitle">
                            <span class="sub-domain">${safeDomain}</span>
                            <span class="sub-category">• ${escapeHtml(e.category)}</span>
                            <span class="sub-visits">• ${e.visit_count} visit${e.visit_count > 1 ? 's' : ''}</span>
                        </div>
                    </div>
                    <div class="row-meta">
                        ${statusBadge}
                        <span class="row-time">${timeFormatted}</span>
                        <a href="${safeUrl}" target="_blank" rel="noopener noreferrer" class="link-icon-btn" title="Open page">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                                <polyline points="15 3 21 3 21 9"/>
                                <line x1="10" y1="14" x2="21" y2="3"/>
                            </svg>
                        </a>
                    </div>
                </li>
            `;
        }).join("");
    }

    function getDomainInitial(domain) {
        if (!domain) return "W";
        const clean = domain.replace(/^www\./, "");
        return clean.charAt(0).toUpperCase();
    }

    function formatTime(isoString) {
        if (!isoString) return "-";
        try {
            const date = new Date(isoString);
            const now = new Date();
            const isToday = date.toDateString() === now.toDateString();

            if (isToday) {
                return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
            }

            const yesterday = new Date();
            yesterday.setDate(now.getDate() - 1);
            if (date.toDateString() === yesterday.toDateString()) {
                return "Yesterday";
            }

            return date.toLocaleDateString([], { month: "short", day: "numeric" });
        } catch (e) {
            return isoString.substring(0, 10);
        }
    }

    function highlightText(text, query) {
        if (!query || !text) return text;
        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, "gi");
        return text.replace(regex, `<span style="background: rgba(10, 132, 255, 0.25); color: #fff; padding: 0 1px; border-radius: 2px;">$1</span>`);
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

    // Search events
    searchInput.addEventListener("input", () => {
        searchClearBtn.style.display = searchInput.value.length > 0 ? "flex" : "none";
        clearTimeout(searchDebounceTimeout);
        searchDebounceTimeout = setTimeout(() => {
            currentPage = 0;
            loadHistory();
        }, 150);
    });

    searchClearBtn.addEventListener("click", () => {
        searchInput.value = "";
        searchClearBtn.style.display = "none";
        searchInput.focus();
        currentPage = 0;
        loadHistory();
    });

    // Segmented Control
    segmentButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            segmentButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentFilterTab = btn.dataset.filter;
            currentPage = 0;
            loadHistory();
        });
    });

    // Category chips
    categoryChips.forEach(chip => {
        chip.addEventListener("click", () => {
            categoryChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            currentCategory = chip.dataset.category;
            currentPage = 0;
            loadHistory();
        });
    });

    // Browser dropdown
    browserDropdown.addEventListener("change", () => {
        currentBrowser = browserDropdown.value;
        currentPage = 0;
        loadHistory();
    });

    // Stepper Pagination
    btnPrev.addEventListener("click", () => {
        if (currentPage > 0) {
            currentPage--;
            loadHistory();
        }
    });

    btnNext.addEventListener("click", () => {
        currentPage++;
        loadHistory();
    });

    // Sync Button
    btnSync.addEventListener("click", async () => {
        syncSvg.classList.add("rotating");
        btnSync.disabled = true;
        try {
            await fetch("/api/sync", { method: "POST" });
            await loadStats();
            await loadHistory();
        } catch (e) {
            console.error("Sync error:", e);
        } finally {
            syncSvg.classList.remove("rotating");
            btnSync.disabled = false;
        }
    });

    // Export popover
    btnExportToggle.addEventListener("click", (e) => {
        e.stopPropagation();
        exportMenu.classList.toggle("show");
    });

    document.addEventListener("click", () => {
        exportMenu.classList.remove("show");
    });

    // Initialize
    loadStats();
    loadHistory();
});
