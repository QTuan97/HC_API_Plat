// static/js/rule_list.js

async function fetchJSON(url, opts = {}) {
  const res = await fetch(url, opts);
  if (!res.ok) throw new Error(await res.text() || res.statusText);
  return res.json();
}

document.addEventListener("DOMContentLoaded", () => {
  const PROJECT_ID     = window.PROJECT_ID;
  const API_BASE       = `/api/projects/${PROJECT_ID}/rules`;
  const tbody          = document.querySelector("#rules-table tbody");
  const editModalEl    = document.getElementById("editRuleModal");
  const editForm       = document.getElementById("edit-rule-form");
  const addEditBtn     = document.getElementById("add-edit-weighted");
  const editContainer  = document.getElementById("edit-weighted-container");
  const editTemplate   = document.getElementById("edit-weighted-template").content;
  const singleRadioE   = document.getElementById("edit-resp-single");
  const weightedRadioE = document.getElementById("edit-resp-weighted");
  const singleSecE     = document.getElementById("edit-single-section");
  const weightedSecE   = document.getElementById("edit-weighted-section");

  if (!tbody || !editModalEl || !editForm) return;
  const editModal = new bootstrap.Modal(editModalEl);
  let rulesData = [];
  let editingId = null;

  function statusClass(code) {
    if (code >= 500) return "bg-danger text-white";
    if (code >= 400) return "bg-warning text-dark";
    if (code >= 200) return "bg-success text-white";
    return "bg-secondary text-white";
  }

  // show/hide & enable/disable edit sections
  function updateSectionInEditModal() {
    const single = singleRadioE.checked;
    // toggle visibility
    singleSecE .style.display = single ? "" : "none";
    weightedSecE.style.display = single ? "none" : "";
    // disable single‐response inputs when in weighted mode
    singleSecE.querySelectorAll("input, textarea").forEach(el => {
      el.disabled = !single;
    });
    // disable weighted controls in single mode (optional)
    weightedSecE.querySelectorAll("input, button").forEach(el => {
      el.disabled = single;
    });
  }
  singleRadioE.addEventListener("change",   updateSectionInEditModal);
  weightedRadioE.addEventListener("change", updateSectionInEditModal);

  // add‐weighted in edit modal
  addEditBtn.onclick = () => {
    if (editContainer.children.length >= 4) return;
    const clone = document.importNode(editTemplate, true);
    clone.querySelector(".entry-index").textContent = editContainer.children.length + 1;
    editContainer.appendChild(clone);
  };
  editContainer.addEventListener("click", e => {
    if (!e.target.classList.contains("remove-weighted")) return;
    e.target.closest(".weighted-entry").remove();
    Array.from(editContainer.children).forEach((ent, i) => {
      ent.querySelector(".entry-index").textContent = i+1;
    });
  });

  // load & render
  async function loadRules(highlightId=null) {
    rulesData = await fetchJSON(API_BASE);
    tbody.innerHTML = rulesData.map(r => `
      <tr class="rule-row" data-id="${r.id}">
        <td>${r.id}</td>
        <td>${r.method}</td>
        <td>${r.path_regex}</td>
        <td>${r.delay ?? (r.body_template.delay||0)}</td>
        <td><span class="badge ${statusClass(r.status_code)}">${r.status_code}</span></td>
        <td>
          <button class="btn btn-sm btn-primary edit-rule">Edit</button>
          <button class="btn btn-sm btn-danger delete-rule">Delete</button>
          <button class="btn btn-sm toggle-rule ${r.enabled ? "btn-warning":"btn-success"}">
            ${r.enabled ? "Disable":"Enable"}
          </button>
        </td>
      </tr>
      <tr class="rule-details" id="rule-details-${r.id}" style="display:none;">
        <td colspan="6">
          <div class="p-3 bg-light border rounded small">
            <p><strong>Headers:</strong></p><pre>${JSON.stringify(r.headers,null,2)}</pre>
            <p><strong>Body Template:</strong></p><pre>${
              Array.isArray(r.body_template)
                ? JSON.stringify(r.body_template,null,2)
                : r.body_template.template
            }</pre>
            <p><strong>Enabled:</strong> ${r.enabled?"Yes":"No"}</p>
          </div>
        </td>
      </tr>`
    ).join("");

    if (highlightId) {
      const row = tbody.querySelector(`tr.rule-row[data-id="${highlightId}"]`);
      if (row) {
        row.classList.add("table-success");
        setTimeout(()=>row.classList.remove("table-success"),1000);
      }
    }
  }

  // delegate clicks
  tbody.addEventListener("click", async e => {
    const btn = e.target;
    const tr  = btn.closest("tr.rule-row");
    if (!tr) return;
    const id = tr.dataset.id;

    if (btn.matches(".delete-rule")) {
      if (!confirm(`Delete rule ${id}?`)) return;
      await fetch(`${API_BASE}/${id}`, { method: "DELETE" });
      return loadRules();
    }

    if (btn.matches(".toggle-rule")) {
      await fetchJSON(`${API_BASE}/${id}/toggle`, { method: "POST" });
      return loadRules(id);
    }

    if (btn.matches(".edit-rule")) {
      editingId = id;
      const r = rulesData.find(x=>String(x.id)===id);
      if (!r) return;

      // set response type
      const isWeighted = Array.isArray(r.body_template);
      singleRadioE.checked   = !isWeighted;
      weightedRadioE.checked = isWeighted;
      updateSectionInEditModal();

      // method/path
      editForm.method.value     = r.method;
      editForm.path_regex.value = r.path_regex;

      if (isWeighted) {
        editContainer.innerHTML = "";
        r.body_template.forEach((entry,i)=>{
          const clone = document.importNode(editTemplate, true);
          clone.querySelector(".entry-index").textContent = i+1;
          clone.querySelector(".weight").value          = entry.weight;
          clone.querySelector('input[name="edit-delays[]"]').value      = entry.delay;
          clone.querySelector('input[name="edit-status_codes[]"]').value = entry.status_code;
          clone.querySelector('textarea[name="edit-hdrs[]"]').value      = JSON.stringify(entry.headers,null,2);
          clone.querySelector('textarea[name="edit-bodies[]"]').value    = entry.template;
          editContainer.appendChild(clone);
        });
      } else {
        editForm.delay.value         = r.delay;
        editForm.status_code.value   = r.status_code;
        editForm.headers.value       = JSON.stringify(r.headers,null,2);
        editForm.body_template.value = r.body_template.template;
      }

      editModal.show();
      return;
    }

    // toggle detail row
    if (!btn.closest("button")) {
      const det = document.getElementById(`rule-details-${id}`);
      if (det) det.style.display = det.style.display==="none"?"table-row":"none";
    }
  });

  // handle edit-form submit
  editForm.addEventListener("submit", async e => {
    e.preventDefault();
    const fd = new FormData(editForm);
    const data = {
      method:     fd.get("method"),
      path_regex: fd.get("path_regex")
    };

    if (weightedRadioE.checked) {
      data.response_type = "weighted";
      data.body_template = Array.from(editContainer.querySelectorAll(".weighted-entry")).map(ent=>({
        weight:      parseInt(ent.querySelector(".weight").value,10)||0,
        delay:       parseInt(ent.querySelector('input[name="edit-delays[]"]').value,10)||0,
        status_code: parseInt(ent.querySelector('input[name="edit-status_codes[]"]').value,10)||200,
        headers:     JSON.parse(ent.querySelector('textarea[name="edit-hdrs[]"]').value||"{}"),
        template:    ent.querySelector('textarea[name="edit-bodies[]"]').value||""
      }));
    } else {
      data.response_type = "single";
      data.delay         = parseInt(fd.get("delay"),10)||0;
      data.status_code   = parseInt(fd.get("status_code"),10)||200;
      data.headers       = JSON.parse(fd.get("headers")||"{}");
      data.body_template = { template: fd.get("body_template") };
    }

    await fetchJSON(`${API_BASE}/${editingId}`, {
      method:  "PUT",
      headers: { "Content-Type":"application/json" },
      body:    JSON.stringify(data)
    });
    editModal.hide();
    loadRules(editingId);
  });

  // initial load
  loadRules();
});