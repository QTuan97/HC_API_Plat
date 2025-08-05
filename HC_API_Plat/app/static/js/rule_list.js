// static/js/rule_list.js

(() => {
  // — fetch helper —
  async function fetchJSON(url, opts = {}) {
    const res = await fetch(url, opts);
    if (!res.ok) throw new Error(await res.text() || res.statusText);
    return res.json();
  }

  // — toast helper —
  function showToast(message, type = "success") {
    let container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      Object.assign(container.style, {
        position: "fixed",
        top: "1rem",
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 2000,
      });
      document.body.appendChild(container);
    }
    const toastEl = document.createElement("div");
    toastEl.className = "toast";
    toastEl.setAttribute("role","alert");
    toastEl.setAttribute("aria-live","assertive");
    toastEl.setAttribute("aria-atomic","true");
    toastEl.innerHTML = `
      <div class="toast-header">
        <strong class="me-auto">${type === "success" ? "✔ Success" : "⚠ Notice"}</strong>
        <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
      </div>
      <div class="toast-body">${message}</div>
    `;
    container.appendChild(toastEl);
    const bsToast = new bootstrap.Toast(toastEl, { delay: 3000 });
    bsToast.show();
    toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
  }

  document.addEventListener("DOMContentLoaded", () => {
    // — DOM refs —
    const PROJECT_ID      = window.PROJECT_ID;
    const API_BASE        = `/api/projects/${PROJECT_ID}/rules`;
    const BASE_URL        = document.getElementById("base-url").textContent;
    const tbody           = document.querySelector("#rules-table tbody");
    const editModalEl     = document.getElementById("editRuleModal");
    const editForm        = document.getElementById("edit-rule-form");
    const addWeightedBtn  = document.getElementById("add-edit-weighted");
    const weightedTmpl    = document.getElementById("edit-weighted-template").content;
    const weightedCtr     = document.getElementById("edit-weighted-container");
    const singleRadio     = document.getElementById("edit-resp-single");
    const weightedRadio   = document.getElementById("edit-resp-weighted");
    const singleSection   = document.getElementById("edit-single-section");
    const weightedSection = document.getElementById("edit-weighted-section");
    const methodSelect    = editForm.querySelector('select[name="method"]');
    const reqBodyGroup    = editModalEl.querySelector(".request-body-group");

    if (!tbody || !editModalEl || !editForm) return;
    const editModal = new bootstrap.Modal(editModalEl);
    let rules = [];
    let currentEditId = null;

    // — Helpers —
    const statusClass = code =>
      code >= 500 ? "bg-danger text-white"
      : code >= 400 ? "bg-warning text-dark"
      : code >= 200 ? "bg-success text-white"
      : "bg-secondary text-white";

    function toggleReqBody() {
      const method = methodSelect.value.toUpperCase();
      if (["POST","PUT","PATCH"].includes(method)) {
        reqBodyGroup.classList.remove("d-none");
      } else {
        reqBodyGroup.classList.add("d-none");
        reqBodyGroup.querySelector("textarea").value = "";
      }
    }

    function toggleResponseUI() {
      const single = singleRadio.checked;
      singleSection.style.display   = single ? "" : "none";
      weightedSection.style.display = single ? "none" : "";
      singleSection.querySelectorAll("input,textarea").forEach(el => el.disabled = !single);
      weightedSection.querySelectorAll("input,button").forEach(el => el.disabled = single);
    }

    // — Bind events —
    methodSelect.addEventListener("change", toggleReqBody);
    singleRadio.addEventListener("change", toggleResponseUI);
    weightedRadio.addEventListener("change", toggleResponseUI);
    addWeightedBtn.addEventListener("click", () => {
      if (weightedCtr.children.length >= 4) return;
      const node = document.importNode(weightedTmpl, true);
      node.querySelector(".entry-index").textContent = weightedCtr.children.length + 1;
      weightedCtr.appendChild(node);
    });
    weightedCtr.addEventListener("click", e => {
      if (!e.target.classList.contains("remove-weighted")) return;
      e.target.closest(".weighted-entry").remove();
      [...weightedCtr.children].forEach((ent,i) => {
        ent.querySelector(".entry-index").textContent = i+1;
      });
    });

    // — Load & render —
    async function loadRules(highlightId) {
      rules = await fetchJSON(API_BASE);
      tbody.innerHTML = rules.map(r => `
        <tr class="rule-row" data-id="${r.id}" data-path="${r.path_regex}">
          <td>${r.id}</td>
          <td>${r.method}</td>
          <td>${r.path_regex}</td>
          <td>${ Array.isArray(r.body_template) ? "Weighted" : "Single" }</td>
          <td>${
                Array.isArray(r.body_template)
                  ? ''
                  : r.delay
              }
          <td>
              ${
                Array.isArray(r.body_template)
                  ? ''
                  : `<span class="badge ${statusClass(r.status_code)}">
                       ${r.status_code}
                     </span>`
              }
          </td>
          <td>
            <button class="btn btn-sm btn-primary edit-rule">Edit</button>
            <button class="btn btn-sm btn-danger delete-rule">Delete</button>
            <button class="btn btn-sm btn-secondary copy-rule">Copy</button>
            <button class="btn btn-sm toggle-rule ${r.enabled?"btn-warning":"btn-success"}">${r.enabled?"Disable":"Enable"}</button>
          </td>
        </tr>
        <tr class="rule-details" id="rule-details-${r.id}" style="display:none;">
          <td colspan="7">
            <div class="p-3 bg-light border rounded small">
              <p><strong>Request Body:</strong></p>
              <pre>${ r.request_body ? JSON.stringify(r.request_body,null,2) : "<em>None</em>" }</pre>
              <p><strong>Headers:</strong></p>
              <pre>${ JSON.stringify(r.headers,null,2) }</pre>
              <p><strong>Body Template:</strong></p>
              <pre>${
                Array.isArray(r.body_template)
                  ? JSON.stringify(r.body_template,null,2)
                  : r.body_template.template
              }</pre>
              <p><strong>Enabled:</strong> ${r.enabled?"Yes":"No"}</p>
            </div>
          </td>
        </tr>
      `).join("");

      if (highlightId) {
        const row = tbody.querySelector(`tr.rule-row[data-id="${highlightId}"]`);
        if (row) {
          row.classList.add("table-success");
          setTimeout(() => row.classList.remove("table-success"), 1000);
        }
      }
    }

    // — Delegate clicks —
    tbody.addEventListener("click", async e => {
      const btn = e.target;
      const tr  = btn.closest("tr.rule-row");
      if (!tr) return;
      const id   = tr.dataset.id;
      const path = tr.dataset.path;

      if (btn.matches(".delete-rule")) {
        if (!confirm(`Delete rule ${id}?`)) return;
        await fetch(`${API_BASE}/${id}`, { method:"DELETE" });
        return loadRules();
      }
      if (btn.matches(".toggle-rule")) {
        await fetchJSON(`${API_BASE}/${id}/toggle`, { method:"POST" });
        return loadRules(id);
      }
      if (btn.matches(".copy-rule")) {
        try {
          await navigator.clipboard.writeText(`${BASE_URL}${path}`);
          showToast(`Copied: ${BASE_URL}${path}`);
        } catch {
          showToast("Copy failed","danger");
        }
        return;
      }
      if (btn.matches(".edit-rule")) {
        currentEditId = id;
        const r = rules.find(x => String(x.id) === id);
        if (!r) return;

        // Reset the form completely
        editForm.reset();
        // Hide & clear request-body
        reqBodyGroup.classList.add("d-none");
        reqBodyGroup.querySelector("textarea").value = "";
        // Clear weighted entries container
        weightedCtr.innerHTML = ""

        // Populate form fields
        editForm.method.value     = r.method;
        editForm.path_regex.value = r.path_regex;

        // Request-body toggle and populate
        toggleReqBody();
        if (r.request_body != null) {
          reqBodyGroup.querySelector("textarea").value = JSON.stringify(r.request_body,null,2);
        }

        // Response section toggle
        const isWeighted = Array.isArray(r.body_template);
        singleRadio.checked   = !isWeighted;
        weightedRadio.checked = isWeighted;
        toggleResponseUI();

        // Populate single or weighted
        if (isWeighted) {
          weightedCtr.innerHTML = "";
          r.body_template.forEach((ent,i) => {
            const node = document.importNode(weightedTmpl, true);
            node.querySelector(".entry-index").textContent = i+1;
            node.querySelector(".weight").value            = ent.weight;
            node.querySelector('input[name="edit-delays[]"]').value      = ent.delay;
            node.querySelector('input[name="edit-status_codes[]"]').value = ent.status_code;
            node.querySelector('textarea[name="edit-hdrs[]"]').value      = JSON.stringify(ent.headers,null,2);
            node.querySelector('textarea[name="edit-bodies[]"]').value    = ent.template;
            weightedCtr.appendChild(node);
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

      // — Toggle details rows —
      if (!btn.closest("button")) {
        const detailRow = document.getElementById(`rule-details-${id}`);
        if (detailRow) {
          detailRow.style.display = detailRow.style.display === "none" ? "table-row" : "none";
        }
      }
    });

    // — Handle edit save —
    editForm.addEventListener("submit", async e => {
      e.preventDefault();
      console.log("[edit] submit handler fired");
      const fd = new FormData(editForm);
      const updateData = {
        method:     fd.get("method"),
        path_regex: fd.get("path_regex")
      };

      if (!reqBodyGroup.classList.contains("d-none")) {
        const rawBody = fd.get("request_body")?.trim();
        console.log("[edit] rawBody:", rawBody);
        if (rawBody) updateData.request_body = rawBody;
      }

      if (weightedRadio.checked) {
        updateData.response_type = "weighted";
        updateData.body_template = [...weightedCtr.children].map(ent => ({
          weight:      +ent.querySelector(".weight").value || 0,
          delay:       +ent.querySelector('input[name="edit-delays[]"]').value || 0,
          status_code: +ent.querySelector('input[name="edit-status_codes[]"]').value || 200,
          headers:     JSON.parse(ent.querySelector('textarea[name="edit-hdrs[]"]').value || "{}"),
          template:    ent.querySelector('textarea[name="edit-bodies[]"]').value || ""
        }));
      } else {
        updateData.response_type = "single";
        updateData.delay         = +fd.get("delay") || 0;
        updateData.status_code   = +fd.get("status_code") || 200;
        updateData.headers       = JSON.parse(fd.get("headers") || "{}");
        updateData.body_template = { template: fd.get("body_template") };
      }

      console.log("[edit] final payload:", updateData);

      try {
        const res = await fetch(`${API_BASE}/${currentEditId}`, {
          method:  "PUT",
          headers: { "Content-Type":"application/json" },
          body:    JSON.stringify(updateData)
        });
        console.log("[edit] HTTP status", res.status);
        const text = await res.text();
        console.log("[edit] response text:", text);
        if (!res.ok) {
          showToast(`Invalid request body JSON form`, "danger");
          return;
        }
      } catch (err) {
        console.error("[edit] network error:", err);
        showToast("Network error", "danger");
        return;
      }

      editModal.hide();
      loadRules(currentEditId);
    });

    // — Initialize —
    loadRules();
    toggleReqBody();
    toggleResponseUI();
  });
})();