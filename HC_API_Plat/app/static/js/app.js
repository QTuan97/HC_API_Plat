async function fetchJSON(url, opts) {
  const res = await fetch(url, opts);
  if (!res.ok) throw await res.text();
  return res.json();
}

document.addEventListener("DOMContentLoaded", () => {
// Projects Page
  const projectForm      = document.getElementById("project-form");
  const projectContainer = document.getElementById("projects-container");
  const editProjModalEl  = document.getElementById("editProjectModal");
  const editProjForm     = document.getElementById("edit-project-form");

  if (projectForm && projectContainer && editProjModalEl && editProjForm) {
    let projectsData = [];
    const editProjModal = new bootstrap.Modal(editProjModalEl);
    let editingProjectId;

    async function loadProjects() {
      projectsData = await fetchJSON("/api/projects");
      projectContainer.innerHTML = projectsData.map(p =>
        `<div class="col">
           <div class="card project-card h-100">
             <div class="card-body d-flex flex-column justify-content-between">
               <div>
                 <h5 class="card-title">${p.name}</h5>
                 <p class="card-text text-muted mb-0">${p.base_url}</p>
                 ${p.description ? `<p class="card-text small mt-1">${p.description}</p>` : ""}
               </div>
               <div class="mt-3 btn-group">
                 <a href="/projects/${p.id}/rules" class="btn btn-outline-primary btn-sm">Open</a>
                 <button class="btn btn-outline-secondary btn-sm edit-project" data-id="${p.id}">Edit</button>
                 <button class="btn btn-outline-danger btn-sm delete-project" data-id="${p.id}">Delete</button>
               </div>
             </div>
           </div>
         </div>`
      ).join("");
    }

    projectForm.addEventListener("submit", async e => {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(projectForm));
      await fetchJSON("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      projectForm.reset();
      loadProjects();
    });

    projectContainer.addEventListener("click", async e => {
      const id = e.target.dataset.id;
      if (e.target.matches(".delete-project")) {
        if (!confirm(`Delete project #${id}?`)) return;
        const res = await fetch(`/api/projects/${id}`, { method: "DELETE" });
        if (!res.ok) return alert(await res.text());
        return loadProjects();
      }
      if (e.target.matches(".edit-project")) {
        const proj = projectsData.find(p => p.id == id);
        editingProjectId = id;
        editProjForm.elements.name.value        = proj.name;
        editProjForm.elements.base_url.value    = proj.base_url;
        editProjForm.elements.description.value = proj.description || "";
        editProjModal.show();
      }
    });

    editProjForm.addEventListener("submit", async e => {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(editProjForm));
      await fetchJSON(`/api/projects/${editingProjectId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      editProjModal.hide();
      loadProjects();
    });

    loadProjects();
    return;
  }

// Rules Page
  const ruleForm        = document.getElementById("rule-form");
  const rulesTbody      = document.querySelector("#rules-table tbody");
  const editRuleModalEl = document.getElementById("editRuleModal");
  const editRuleForm    = document.getElementById("edit-rule-form");
  const projMatch       = location.pathname.match(/\/projects\/(\d+)\/rules/);
  const PROJECT_ID      = projMatch ? projMatch[1] : null;

  if (ruleForm && rulesTbody && editRuleModalEl && editRuleForm && PROJECT_ID) {
    let rulesData = [];
    const editRuleModal = new bootstrap.Modal(editRuleModalEl);
    let editingRuleId;

    async function loadRules() {
      rulesData = await fetchJSON(`/api/projects/${PROJECT_ID}/rules`);
      rulesTbody.innerHTML = rulesData.map(r =>
        `<tr data-id="${r.id}">
           <td>${r.id}</td>
           <td>${r.method}</td>
           <td>${r.path_regex}</td>
           <td>${r.delay}</td>
           <td>${r.status_code}</td>
           <td>
             <button class="btn btn-sm btn-primary edit-rule">Edit</button>
             <button class="btn btn-sm btn-danger delete-rule">Delete</button>
             <button class="btn btn-sm ${r.enabled ? "btn-warning" : "btn-success"} toggle-rule">
               ${r.enabled ? "Disable" : "Enable"}
             </button>
           </td>
         </tr>`
      ).join("");
    }

    ruleForm.addEventListener("submit", async e => {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(ruleForm));
      data.delay         = parseInt(data.delay, 10) || 0;
      data.status_code   = parseInt(data.status_code, 10) || 200;
      data.headers       = JSON.parse(data.headers || "{}");
      data.body_template = { template: data.body_template.trim() };

      await fetchJSON(`/api/projects/${PROJECT_ID}/rules`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      ruleForm.reset();
      loadRules();
    });

    rulesTbody.addEventListener("click", async e => {
      const tr = e.target.closest("tr");
      if (!tr) return;
      const id = tr.dataset.id;

      if (e.target.matches(".delete-rule")) {
        if (!confirm(`Delete rule #${id}?`)) return;
        const res = await fetch(`/api/projects/${PROJECT_ID}/rules/${id}`, { method: "DELETE" });
        if (!res.ok) return alert(await res.text());
        return loadRules();
      }
      if (e.target.matches(".toggle-rule")) {
        await fetchJSON(`/api/projects/${PROJECT_ID}/rules/${id}/toggle`, { method: "POST" });
        return loadRules();
      }
      if (e.target.matches(".edit-rule")) {
        const rule = rulesData.find(r => r.id == id);
        editingRuleId = id;
        const fm = editRuleForm.elements;
        fm.method.innerHTML = ["GET","POST","PUT","DELETE","PATCH"]
          .map(m => `<option${m===rule.method ? " selected" : ""}>${m}</option>`)
          .join("");
        fm.path_regex.value    = rule.path_regex;
        fm.delay.value         = rule.delay;
        fm.status_code.value   = rule.status_code;
        fm.headers.value       = JSON.stringify(rule.headers, null, 2);
        fm.body_template.value = rule.body_template.template;
        editRuleModal.show();
      }
    });

    editRuleForm.addEventListener("submit", async e => {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(editRuleForm));
      data.delay         = parseInt(data.delay, 10) || 0;
      data.status_code   = parseInt(data.status_code, 10) || 200;
      data.headers       = JSON.parse(data.headers || "{}");
      data.body_template = { template: data.body_template.trim() };

      await fetchJSON(`/api/projects/${PROJECT_ID}/rules/${editingRuleId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      editRuleModal.hide();
      loadRules();
    });

    loadRules();
    return;
  }

// Logs Page
  const logsTbody = document.querySelector("#logs-table tbody");
  const clearBtn  = document.getElementById("clear-logs");

  if (logsTbody && clearBtn) {
    async function loadLogs() {
      const logs = await fetchJSON("/api/logs");
      logsTbody.innerHTML = logs.map(l =>
        `<tr>
           <td>${l.id}</td>
           <td>${new Date(l.timestamp).toLocaleString()}</td>
           <td>${l.method}</td>
           <td>${l.path}</td>
           <td>${l.matched_rule_id || ""}</td>
           <td>${l.status_code}</td>
         </tr>`
      ).join("");
    }

    clearBtn.addEventListener("click", async () => {
      if (!confirm("Clear all logs?")) return;
      await fetchJSON("/api/logs", { method: "DELETE" });
      loadLogs();
    });

    loadLogs();
    setInterval(loadLogs, 5000);
  }
});