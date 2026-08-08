const documentListEl = document.getElementById("documentList");
const uploadStatusEl = document.getElementById("uploadStatus");
const docCountEl     = document.getElementById("docCount");
const fileSlotEl     = document.getElementById("fileSlot");
const fileSlotTextEl = document.getElementById("fileSlotText");
const findingsSection = document.getElementById("findingsSection");
const answerBoxEl    = document.getElementById("answerBox");
const sourcesHeaderEl = document.getElementById("sourcesHeader");
const sourcesBoxEl   = document.getElementById("sourcesBox");

let knownDocs = {}; // stem -> { display_name, selected, stats }

// ---------- File input label ----------

document.getElementById("fileInput").addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (file) {
    fileSlotTextEl.textContent = file.name;
    fileSlotEl.classList.add("has-file");
  } else {
    fileSlotTextEl.textContent = "Choose a PDF file…";
    fileSlotEl.classList.remove("has-file");
  }
});

// ---------- Documents ----------

async function loadDocuments() {
  const res = await fetch("/documents");
  const registry = await res.json();

  for (const stem in registry) {
    knownDocs[stem] = {
      display_name: registry[stem].display_name,
      selected: knownDocs[stem]?.selected ?? true,
      stats: registry[stem].stats,
    };
  }

  renderDocumentList();
}

function renderDocumentList() {
  const stems = Object.keys(knownDocs);
  docCountEl.textContent = `${stems.length} document${stems.length === 1 ? "" : "s"} on file`;

  if (!stems.length) {
    documentListEl.innerHTML = '<p class="empty-note">No documents processed yet. Add one above to begin.</p>';
    return;
  }

  documentListEl.innerHTML = "";
  stems.forEach((stem) => {
    const doc = knownDocs[stem];

    const card = document.createElement("div");
    card.className = "doc-card";

    const head = document.createElement("label");
    head.className = "doc-card-head";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = doc.selected;
    checkbox.addEventListener("change", () => {
      knownDocs[stem].selected = checkbox.checked;
    });

    const name = document.createElement("span");
    name.className = "doc-name";
    name.textContent = doc.display_name;

    head.appendChild(checkbox);
    head.appendChild(name);
    card.appendChild(head);

    if (doc.stats) {
      const stats = document.createElement("div");
      stats.className = "doc-stats";
      stats.innerHTML = `
        <span>Pages <b>${doc.stats.pages}</b></span>
        <span>Words <b>${doc.stats.words}</b></span>
        <span>Chunks <b>${doc.stats.chunks}</b></span>
        <span>Avg chunk <b>${doc.stats.avg_chunk_words}</b>w</span>
        <span>Embed dim <b>${doc.stats.embedding_dim}</b></span>
      `;
      card.appendChild(stats);
    }

    documentListEl.appendChild(card);
  });
}

// ---------- Upload ----------

document.getElementById("uploadBtn").addEventListener("click", async () => {
  const fileInput = document.getElementById("fileInput");
  if (!fileInput.files.length) {
    uploadStatusEl.textContent = "Choose a PDF first.";
    uploadStatusEl.classList.add("error");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  uploadStatusEl.classList.remove("error");
  uploadStatusEl.textContent = "Processing…";

  try {
    const res = await fetch("/upload", { method: "POST", body: formData });
    const data = await res.json();

    if (data.stem) {
      uploadStatusEl.textContent = `${data.filename} processed successfully.`;
      fileInput.value = "";
      fileSlotTextEl.textContent = "Choose a PDF file…";
      fileSlotEl.classList.remove("has-file");
      await loadDocuments();
    } else {
      uploadStatusEl.textContent = "Upload failed.";
      uploadStatusEl.classList.add("error");
    }
  } catch (err) {
    uploadStatusEl.textContent = "Upload failed — check the server is running.";
    uploadStatusEl.classList.add("error");
  }
});

// ---------- Ask ----------

document.getElementById("askBtn").addEventListener("click", async () => {
  const question = document.getElementById("questionInput").value.trim();
  if (!question) return;

  const mode = document.querySelector('input[name="mode"]:checked').value;
  const selectedStems = Object.keys(knownDocs).filter((s) => knownDocs[s].selected);

  findingsSection.hidden = false;
  answerBoxEl.textContent = "Searching…";
  sourcesHeaderEl.hidden = true;
  sourcesBoxEl.innerHTML = "";

  try {
    const res = await fetch("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: question,
        doc_stems: selectedStems.length ? selectedStems : null,
        mode: mode,
      }),
    });
    const data = await res.json();

    answerBoxEl.textContent = data.answer || "No answer returned.";

    const sources = data.sources || [];
    if (sources.length) {
      sourcesHeaderEl.hidden = false;
      sources.forEach((src, i) => {
        const stub = document.createElement("div");
        stub.className = "stub";
        stub.innerHTML = `
          <div class="stub-num">${String(i + 1).padStart(2, "0")}</div>
          <div class="stub-head">
            <span class="stub-file">${src.filename || "—"}</span>
            <span class="stub-pages">pp. ${src.pages || "—"}</span>
          </div>
          <div class="stub-preview">${src.preview || ""}</div>
        `;
        sourcesBoxEl.appendChild(stub);
      });
    }
  } catch (err) {
    answerBoxEl.textContent = "Something went wrong — check the server is running.";
  }
});

loadDocuments();