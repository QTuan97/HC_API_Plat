(async function(){
  // — fetchJSON helper —
  async function fetchJSON(url, opts) {
    const res = await fetch(url, opts);
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || res.statusText);
    }
    return res.json();
  }

  // — simple toast notifier —
  function showToast(message, type="danger") {
  // Create container if needed
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }

  // Build the toast element
  const toastEl = document.createElement("div");
  toastEl.className = "toast";
  toastEl.setAttribute("role", "alert");
  toastEl.setAttribute("aria-live", "assertive");
  toastEl.setAttribute("aria-atomic", "true");
  toastEl.innerHTML = `
    <div class="toast-header">
      <!-- You can switch icons based on 'type' if you like -->
      <strong class="me-auto">${type === "danger" ? "Error" : "Notice"}</strong>
      <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
    <div class="toast-body">
      ${message}
    </div>
  `;

  container.appendChild(toastEl);

  // Initialize & show
  const bsToast = new bootstrap.Toast(toastEl, { delay: 4000 });
  bsToast.show();

  // Clean up from the DOM after hide
  toastEl.addEventListener('hidden.bs.toast', () => {
    toastEl.remove();
  });
  }

  // — grab DOM refs —
  const PROJECT_ID    = window.PROJECT_ID;
  const form          = document.getElementById("rule-form");
  const singleRadio   = document.getElementById("resp-single");
  const weightedRadio = document.getElementById("resp-weighted");
  const addBtn        = document.getElementById("add-weighted");
  const container     = document.getElementById("weighted-container");
  const template      = document.getElementById("weighted-template").content;

  if (!form || !PROJECT_ID) return;

  // — Toggle logic —
  function updateSection() {
    document.getElementById("single-section").style.display   =
      singleRadio.checked   ? "" : "none";
    document.getElementById("weighted-section").style.display =
      weightedRadio.checked ? "" : "none";
  }
  singleRadio.addEventListener("change", updateSection);
  weightedRadio.addEventListener("change", updateSection);

  // — Weighted entries management —
  function updateAddButton() {
    addBtn.style.display = container.children.length >= 4 ? "none" : "";
  }
  addBtn.onclick = () => {
    if (container.children.length >= 4) return;
    const clone = document.importNode(template, true);
    clone.querySelector(".entry-index").textContent = container.children.length + 1;
    container.appendChild(clone);
    updateAddButton();
  };
  container.addEventListener("click", e => {
    if (!e.target.classList.contains("remove-weighted")) return;
    e.target.closest(".weighted-entry").remove();
    Array.from(container.children).forEach((ent,i) => {
      ent.querySelector(".entry-index").textContent = i+1;
    });
    updateAddButton();
  });

  // — Form submission (single bound) —
  if (!form._ruleFormBound) {
    form._ruleFormBound = true;
    form.addEventListener("submit", async e => {
      e.preventDefault();

      // validate weights
      if (weightedRadio.checked) {
        const total = Array.from(container.querySelectorAll(".weight"))
          .map(i=>parseInt(i.value,10)||0)
          .reduce((a,b)=>a+b,0);
        if (total !== 100) {
          return showToast(`Total weight must equal 100% (got ${total}%)`);
        }
      }

      // build payload
      const fd = new FormData(form);
      const payload = {
        method:     fd.get("method"),
        path_regex: fd.get("path_regex")
      };

      if (weightedRadio.checked) {
        payload.response_type = "weighted";
        payload.body_template = Array.from(container.querySelectorAll(".weighted-entry")).map(ent => ({
          weight:      parseInt(ent.querySelector(".weight").value,10)||0,
          delay:       parseInt(ent.querySelector('input[name="delays[]"]').value,10)||0,
          status_code: parseInt(ent.querySelector('input[name="status_codes[]"]').value,10)||200,
          headers:     JSON.parse(ent.querySelector('textarea[name="hdrs[]"]').value||"{}"),
          template:    ent.querySelector('textarea[name="bodies[]"]').value||""
        }));
      } else {
        payload.response_type = "single";
        payload.delay         = parseInt(fd.get("delay"),10)||0;
        payload.status_code   = parseInt(fd.get("status_code"),10)||200;
        payload.headers       = JSON.parse(fd.get("headers")||"{}");
        payload.body_template = { template: fd.get("body_template") };
      }

      // send to API
      try {
        await fetchJSON(`/api/projects/${PROJECT_ID}/rules`, {
          method:  "POST",
          headers: { "Content-Type":"application/json" },
          body:    JSON.stringify(payload)
        });
        window.location.href = `/projects/${PROJECT_ID}/rules`;
      } catch (err) {
        showToast(err.message);
      }
    });
  }

  // initialize
  updateSection();
  updateAddButton();
})();