async function fetchJSON(url, opts) {
  const res = await fetch(url, opts);
  if (!res.ok) throw await res.text();
  return res.json();
}

const projMatch = location.pathname.match(/\/ui\/projects\/(\d+)\/rules/);
const PROJECT_ID = projMatch ? projMatch[1] : null;
let rulesData = [];
let editingRuleId;

document.addEventListener("DOMContentLoaded", () => {
  const ruleForm = document.getElementById("rule-form");
  const rulesTbody = document.querySelector("#rules-table tbody");
  const editRuleModalEl = document.getElementById("editRuleModal");
  const editRuleForm = document.getElementById("edit-rule-form");

  function getStatusColorClass(status) {
  if (typeof status !== "number") return "bg-secondary";
  if (status >= 500) return "bg-danger";
  if (status >= 400) return "bg-warning text-dark";
  if (status >= 200) return "bg-success";
  return "bg-secondary";
    }


  if (!ruleForm || !rulesTbody || !editRuleModalEl || !editRuleForm || !PROJECT_ID) {
    console.warn("Missing rule DOM elements");
    return;
  }

  const editRuleModal = new bootstrap.Modal(editRuleModalEl);

  async function loadRules(highlightId = null) {
    rulesData = await fetchJSON(`/api/projects/${PROJECT_ID}/rules`);
    rulesTbody.innerHTML = rulesData.map(r => {
      const detailRow = `<tr class="rule-details" id="rule-details-${r.id}" style="display:none;">
        <td colspan="6">
          <div class="p-3 bg-light border rounded small">
            <p><strong>Headers:</strong></p>
            <pre>${JSON.stringify(r.headers, null, 2)}</pre>
            <p><strong>Body Template:</strong></p>
            <pre>${r.body_template.template}</pre>
            <p><strong>Enabled:</strong> ${r.enabled ? "Yes" : "No"}</p>
          </div>
        </td>
      </tr>`;

      const mainRow = `<tr class="rule-row" data-id="${r.id}">
        <td>${r.id}</td>
        <td>${r.method}</td>
        <td>${r.path_regex}</td>
        <td>${r.delay}</td>
        <td><span class="badge ${getStatusColorClass(r.status_code)}">${r.status_code}</span></td>
        <td>
          <button class="btn btn-sm btn-primary edit-rule">Edit</button>
          <button class="btn btn-sm btn-danger delete-rule">Delete</button>
          <button class="btn btn-sm ${r.enabled ? "btn-warning" : "btn-success"} toggle-rule">
            ${r.enabled ? "Disable" : "Enable"}
          </button>
        </td>
      </tr>`;

      return mainRow + detailRow;
    }).join("");

    if (highlightId) {
      setTimeout(() => {
        const row = document.querySelector(`tr[data-id="${highlightId}"]`);
        if (row) {
          row.scrollIntoView({ behavior: "smooth", block: "center" });
          toggleRuleDetails(highlightId);
          row.classList.add("table-success");
          setTimeout(() => row.classList.remove("table-success"), 1000);
        }
      }, 50);
    }
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
    if (!tr || !tr.classList.contains("rule-row")) return;

    const id = tr.getAttribute("data-id");
    const target = e.target;

    if (target.matches(".delete-rule")) {
      if (!confirm(`Delete rule #${id}?`)) return;
      const res = await fetch(`/api/projects/${PROJECT_ID}/rules/${id}`, { method: "DELETE" });
      if (!res.ok) return alert(await res.text());
      return loadRules();
    }

    if (target.matches(".toggle-rule")) {
      await fetchJSON(`/api/projects/${PROJECT_ID}/rules/${id}/toggle`, { method: "POST" });
      return loadRules(id);
    }

    if (target.matches(".edit-rule")) {
      const rule = rulesData.find(r => r.id == id);
      editingRuleId = id;
      const fm = editRuleForm.elements;
      fm.method.innerHTML = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        .map(m => `<option${m === rule.method ? " selected" : ""}>${m}</option>`)
        .join("");
      fm.path_regex.value = rule.path_regex;
      fm.delay.value = rule.delay;
      fm.status_code.value = rule.status_code;
      fm.headers.value = JSON.stringify(rule.headers, null, 2);
      fm.body_template.value = rule.body_template.template;
      editRuleModal.show();
      return;
    }

    if (!target.closest("button")) {
      toggleRuleDetails(id);
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
    loadRules(editingRuleId);
  });

  loadRules();
});

window.toggleRuleDetails = function(id) {
  const row = document.getElementById("rule-details-" + id);
  if (row) {
    row.style.display = row.style.display === "none" ? "table-row" : "none";
  }
};
