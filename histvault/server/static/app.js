/* HistVault Web Client Controller */
document.addEventListener("DOMContentLoaded", () => {
    let currentPage = 0;
    const pageSize = 50;
    let currentFilterTab = "all"; // all | deleted | active
    let searchDebounceTimeout = null;

    // DOM Elements
    const statTotal = document.getElementById("stat-total");
    const statDeleted = document.getElementById("stat-deleted");
    const statActive = document.getElementById("stat-active");
    const statVisits = document.getElementById("stat-visits");
    const statDomains = document.getElementById("stat-domains");

    const searchInput = document.getElementById("search-input");
    const browserFilter = document.getElementById("browser-filter");
    const categoryFilter = document.getElementById("category-filter");
    const tabPills = document.querySelectorAll(".tab-pills .pill");
    const tbody = document.getElementById("history-tbody");
    const resultsCount = document.getElementById("results-count");
    const btnSync = document.getElementById("btn-sync");
    const syncIcon = document.getElementById("sync-icon");
    const btnPrev = document.getElementById("btn-prev");
    const btnNext = document.getElementById("btn-next");
    const pageIndicator = document.getElementById("page-indicator");

    // Fetch and display vault statistics
    async function loadStats() {
        try {
            const res = await fetch("/api/stats");
            const data = await res.json();
            statTotal.textContent = Number(data.total_urls || 0).toLocaleString();
            statDeleted.textContent = Number(data.deleted_preserved_urls || 0).toLocaleString();
            statActive.textContent = Number(data.active_urls || 0).toLocaleString();
            statVisits.textContent = Number(data.total_visits || 0).toLocaleString();
            statDomains.textContent = `across ${Number(data.unique_domains || 0).toLocaleString()} domains`;
        } catch (e) {
            console.error("Failed to load stats:", e);
        }
    }

    // Fetch history records based on active filters and page
    async function loadHistory() {
        const query = searchInput.value.trim();
        const browser = browserFilter.value;
        const category = categoryFilter.value;
        const offset = currentPage * pageSize;

        let url = `/api/history?limit=${pageSize}&offset=${offset}`;
        if (query) url += `&q=${encodeURIComponent(query)}`;
        if (browser !== "all") url += `&browser=${encodeURIComponent(browser)}`;
        if (category !== "all") url += `&category=${encodeURIComponent(category)}`;

        if (currentFilterTab === "deleted") {
            url += "&deleted_only=true";
        } else if (currentFilterTab === "active") {
            url += "&active_only=true";
        }

        resultsCount.textContent = "Fetching records...";

        try {
            const res = await fetch(url);
            const data = await res.json();
            renderTable(data.entries);
            resultsCount.textContent = `Displaying ${data.entries.length} records (Page ${currentPage + 1})`;

            btnPrev.disabled = currentPage === 0;
            btnNext.disabled = data.entries.length < pageSize;
            pageIndicator.textContent = `Page ${currentPage + 1}`;
        } catch (e) {
            console.error("Failed to load history:", e);
            tbody.innerHTML = `<tr><td colspan="7" style="color: #f87171; text-align: center; padding: 30px;">Error loading data from vault.</td></tr>`;
        }
    }

    // Render table rows
    function renderTable(entries) {
        if (!entries || entries.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; padding: 40px; color: #94a3b8;">
                        No history records found matching your filters.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = entries.map(e => {
            const isDel = e.is_deleted_from_browser;
            const badgeClass = isDel ? "badge-deleted" : "badge-active";
            const badgeLabel = isDel ? "🔴 PRESERVED" : "🟢 ACTIVE";
            const dateStr = e.last_visit_utc ? e.last_visit_utc.replace("T", " ").substring(0, 19) : "-";
            const safeTitle = escapeHtml(e.title || e.url);

            return `
                <tr>
                    <td><span class="badge ${badgeClass}" title="${isDel ? 'History deleted from browser, permanently saved in Vault' : 'Still in browser history'}">${badgeLabel}</span></td>
                    <td><span class="badge-browser">${escapeHtml(e.browser_name)}</span></td>
                    <td><code>${escapeHtml(e.domain)}</code></td>
                    <td>
                        <div class="url-title">${safeTitle}</div>
                        <a href="${escapeHtml(e.url)}" target="_blank" rel="noopener noreferrer" class="url-link">${escapeHtml(e.url)}</a>
                    </td>
                    <td><span class="badge-category">${escapeHtml(e.category)}</span></td>
                    <td style="font-weight: 600;">${e.visit_count}</td>
                    <td style="color: #94a3b8; font-size: 12px;">${dateStr}</td>
                </tr>
            `;
        }).join("");
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

    // Event listeners
    searchInput.addEventListener("input", () => {
        clearTimeout(searchDebounceTimeout);
        searchDebounceTimeout = setTimeout(() => {
            currentPage = 0;
            loadHistory();
        }, 300);
    });

    browserFilter.addEventListener("change", () => {
        currentPage = 0;
        loadHistory();
    });

    categoryFilter.addEventListener("change", () => {
        currentPage = 0;
        loadHistory();
    });

    tabPills.forEach(pill => {
        pill.addEventListener("click", () => {
            tabPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            currentFilterTab = pill.dataset.filter;
            currentPage = 0;
            loadHistory();
        });
    });

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

    // Trigger sync
    btnSync.addEventListener("click", async () => {
        syncIcon.textContent = "⏳";
        btnSync.disabled = true;
        try {
            const res = await fetch("/api/sync", { method: "POST" });
            const data = await res.json();
            await loadStats();
            await loadHistory();
            alert(`Sync Complete!\n- New records: ${data.new_urls}\n- Updated: ${data.updated_urls}\n- Detected Deleted: ${data.newly_detected_deleted}\n- Total Preserved: ${data.total_preserved_urls}`);
        } catch (e) {
            alert("Error syncing history: " + e);
        } finally {
            syncIcon.textContent = "🔄";
            btnSync.disabled = false;
        }
    });

    // Initial load
    loadStats();
    loadHistory();
});
