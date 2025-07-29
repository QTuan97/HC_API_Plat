async function fetchJSON(url, opts = {}) {
  opts.headers = {
    ...(opts.headers || {}),
    "Accept": "application/json"
  };
  const res = await fetch(url, opts);
  if (!res.ok) throw await res.text();
  return res.json();
}

document.addEventListener("DOMContentLoaded", () => {
  const API_BASE = "/api/projects";

  const projectForm      = document.getElementById("project-form");
  const projectContainer = document.getElementById("projects-container");
  const editProjModalEl  = document.getElementById("editProjectModal");
  const editProjForm     = document.getElementById("edit-project-form");

  if (!projectForm || !projectContainer || !editProjModalEl || !editProjForm) return;

  let projectsData = [];
  const editProjModal = new bootstrap.Modal(editProjModalEl);
  let editingProjectId;

  async function loadProjects() {
    projectsData = await fetchJSON(API_BASE);
    projectContainer.innerHTML = projectsData.map(p =>
      `<div class="col">
         <div class="card project-card h-100">
           <div class="card-body d-flex flex-column justify-content-between">
             <div>
               <h5 class="card-title">${p.name}</h5>
               ${p.description ? `<p class="card-text small mt-1">${p.description}</p>` : ""}
             </div>
             <div class="mt-3 btn-group">
               <a href="/ui/projects/${p.id}/rules" class="btn btn-outline-primary btn-sm">Open</a>
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
    const errorEl = document.getElementById("project-error");
    const nameInput = projectForm.querySelector('input[name="name"]');
    const data = Object.fromEntries(new FormData(projectForm));
    const newName = data.name.trim().toLowerCase();

    const exists = projectsData.some(p => p.name.toLowerCase() === newName);
    if (exists) {
      nameInput.classList.add("is-invalid");
      errorEl.textContent = `Project "${newName}" already exists.`;
      errorEl.style.display = "block";
      return;
    }

    nameInput.classList.remove("is-invalid");
    errorEl.textContent = "";
    errorEl.style.display = "none";

    data.name = newName;
    await fetchJSON(API_BASE, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    projectForm.reset();
    loadProjects();
  });

  projectContainer.addEventListener("click", async e => {
    const id = e.target.dataset.id;
    if (!id) return;

    if (e.target.matches(".delete-project")) {
      if (!confirm(`Delete project #${id}?`)) return;
      await fetch(`${API_BASE}/${id}`, { method: "DELETE" });
      return loadProjects();
    }

    if (e.target.matches(".edit-project")) {
      const proj = projectsData.find(p => p.id == id);
      editingProjectId = id;
      editProjForm.elements.name.value = proj.name;
      editProjForm.elements.description.value = proj.description || "";
      editProjModal.show();
    }
  });

  editProjForm.addEventListener("submit", async e => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(editProjForm));
    await fetchJSON(`${API_BASE}/${editingProjectId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    editProjModal.hide();
    loadProjects();
  });

  loadProjects();
});
