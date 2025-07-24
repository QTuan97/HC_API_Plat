async function fetchJSON(url, opts) {
  const res = await fetch(url, opts);
  if (!res.ok) throw await res.text();
  return res.json();
}

document.addEventListener("DOMContentLoaded", () => {
  // Rules page
  if (location.pathname.endsWith("/rules")) {
    const form = document.getElementById("rule-form");
    const tbody = document.querySelector("#rules-table tbody");
    let editingId = null;
    let currentRules = [];

    async function loadRules() {
      currentRules = await fetchJSON("/api/rules");
      tbody.innerHTML = currentRules.map(r =>
        `<tr data-id="${r.id}">
           <td>${r.id}</td>
           <td>${r.method}</td>
           <td>${r.path_regex}</td>
           <td>${r.delay}</td>
           <td>${r.status_code}</td>
           <td>
             <button class="btn btn-sm btn-primary edit-rule">Edit</button>
             <button class="btn btn-sm btn-danger delete-rule">Delete</button>
           </td>
         </tr>`
      ).join("");
    }

    form.onsubmit = async e => {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(form));
      data.delay         = parseInt(data.delay,10) || 0;
      data.status_code   = parseInt(data.status_code,10) || 200;
      data.headers       = JSON.parse(data.headers || "{}");
      data.body_template = { template: data.body_template.trim() };

      const url    = editingId ? `/api/rules/${editingId}` : "/api/rules";
      const method = editingId ? "PUT"             : "POST";

      await fetchJSON(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(data),
      });

      editingId = null;
      form.reset();
      form.querySelector("button[type=submit]").innerText = "Add Rule";
      loadRules();
    };

    tbody.addEventListener("click", async e => {
      const tr = e.target.closest("tr");
      const id = tr.dataset.id;

      if (e.target.matches(".delete-rule")) {
        const res = await fetch(`/api/rules/${id}`, { method: "DELETE" });
        if (!res.ok) return alert(await res.text());
        return loadRules();
      }

      if (e.target.matches(".edit-rule")) {
        const r = currentRules.find(x => x.id == id);
        form.method.value        = r.method;
        form.path_regex.value    = r.path_regex;
        form.delay.value         = r.delay;
        form.status_code.value   = r.status_code;
        form.headers.value       = JSON.stringify(r.headers, null, 2);
        form.body_template.value = r.body_template.template;
        editingId = id;
        form.querySelector("button[type=submit]").innerText = "Update Rule";
      }
    });

    loadRules();
  }

  // Logs page
  if (location.pathname.endsWith("/logs")) {
    const tbody = document.querySelector("#logs-table tbody");
    const clearBtn = document.getElementById("clear-logs");

    async function loadLogs() {
      const logs = await fetchJSON("/api/logs");
      tbody.innerHTML = logs.map(l =>
        `<tr>
           <td>${l.id}</td>
           <td>${new Date(l.timestamp).toLocaleString()}</td>
           <td>${l.method}</td>
           <td>${l.path}</td>
           <td>${l.matched_rule_id||""}</td>
         </tr>`
      ).join("");
    }

    clearBtn.onclick = async () => {
      if (!confirm("Clear all logs?")) return;
      await fetchJSON("/api/logs", { method: "DELETE" });
      loadLogs();
    };

    loadLogs();

    // Logs updated each 5 seconds
    setInterval(loadLogs, 5000);
  }
});