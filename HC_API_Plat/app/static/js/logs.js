document.addEventListener("DOMContentLoaded", () => {
  const clearBtn = document.getElementById("clear-logs");
  const liveToggle = document.getElementById("live-toggle");
  const logsTbody = document.querySelector("#logs-table tbody");
  const paginationInfo = document.getElementById("pagination-info");
  const prevBtn = document.getElementById("prev-page");
  const nextBtn = document.getElementById("next-page");

  let liveMode = true;
  let currentPage = 1;
  const logsPerPage = 20;
  let totalLogs = 0;
  let cachedLogs = [];

  function getStatusColorClass(status) {
    if (typeof status !== "number") return "bg-secondary";
    if (status >= 500) return "bg-danger";
    if (status >= 400) return "bg-warning text-dark";
    if (status >= 200) return "bg-success";
    return "bg-secondary";
  }

  function renderLogs(logs) {
    logsTbody.innerHTML = logs.map((log, index) => {
      const displayNo = (currentPage - 1) * logsPerPage + (index + 1);
      const status = log.status_code ?? "-";
      const statusClass = getStatusColorClass(status);
      return `
        <tr>
          <td>${displayNo}</td>
          <td>${new Date(log.timestamp).toLocaleString()}</td>
          <td>${log.method}</td>
          <td>${log.path}</td>
          <td><span class="badge ${statusClass}">${status}</span></td>
          <td>
            <button class="btn btn-outline-primary btn-sm" onclick="toggleDetails(${log.id})">View Details</button>
          </td>
        </tr>
        <tr id="details-${log.id}" style="display:none;">
          <td colspan="6">
            <strong>Headers:</strong>
            <pre>${JSON.stringify(log.headers, null, 2)}</pre>
            <strong>Query:</strong>
            <pre>${JSON.stringify(log.query, null, 2)}</pre>
            <strong>Body:</strong>
            <pre>${JSON.stringify(log.body, null, 2)}</pre>
            <strong>Response:</strong>
            <pre>${JSON.stringify(log.response?.body ?? {}, null, 2)}</pre>
          </td>
        </tr>
      `;
    }).join("");
  }

  async function fetchLogs() {
    try {
      const res = await fetch(`/api/logs?page=${currentPage}&limit=${logsPerPage}&_=${Date.now()}`);
      const { logs, total } = await res.json();
      cachedLogs = logs;
      totalLogs = total;
      if (liveMode) {
        renderLogs(cachedLogs);
        updatePaginationDisplay();
      }
    } catch (err) {
      console.error("Failed to fetch logs:", err);
    }
  }

  function updatePaginationDisplay() {
    const totalPages = Math.ceil(totalLogs / logsPerPage);
    paginationInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
  }

  clearBtn.addEventListener("click", async () => {
    if (!confirm("Clear all logs?")) return;
    const res = await fetch("/api/logs", { method: "DELETE" });
    if (res.ok) {
      currentPage = 1;
      cachedLogs = [];
      renderLogs([]);
      updatePaginationDisplay();
    }
  });

  liveToggle.addEventListener("change", () => {
    liveMode = liveToggle.checked;
    if (liveMode) {
      renderLogs(cachedLogs);
      updatePaginationDisplay();
    }
  });

  prevBtn.addEventListener("click", () => {
    if (currentPage > 1) {
      currentPage--;
      fetchLogs();
    }
  });

  nextBtn.addEventListener("click", () => {
    currentPage++;
    fetchLogs();
  });

  setInterval(fetchLogs, 3000);
  fetchLogs();
});

function toggleDetails(id) {
  const row = document.getElementById("details-" + id);
  if (!row) return;
  row.style.display = row.style.display === "none" ? "table-row" : "none";
}
