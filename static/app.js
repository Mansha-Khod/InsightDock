const documentListEl = document.getElementById("documentList");
const uploadStatusEl = document.getElementById("uploadStatus");
const answerBoxEl    = document.getElementById("answerBox");
const sourcesBoxEl   = document.getElementById("sourcesBox");

let knownDocs = {}; 

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
  documentListEl.innerHTML = "";
  for (const stem in knownDocs) {
    const doc = knownDocs[stem];

    const card = document.createElement("div");
    card.className = "doc-card";

    const header = document.createElement("label");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = doc.selected;
    checkbox.addEventListener("change", () => {
      knownDocs[stem].selected = checkbox.checked;
    });
    header.appendChild(checkbox);
    header.append(" " + doc.display_name);
    card.appendChild(header);

    if (doc.stats) {
      const statsRow = document.createElement("div");
      statsRow.className = "doc-stats";
      statsRow.innerHTML = `
        <span>Pages: <b>${doc.stats.pages}</b></span>
        <span>Words: <b>${doc.stats.words}</b></span>
        <span>Chunks: <b>${doc.stats.chunks}</b></span>
        <span>Avg Chunk: <b>${doc.stats.avg_chunk_words}</b> words</span>
        <span>Embed Dim: <b>${doc.stats.embedding_dim}</b></span>
      `;
      card.appendChild(statsRow);
    }

    documentListEl.appendChild(card);
  }
}

document.getElementById("uploadBtn").addEventListener("click", async () => {
  const fileInput = document.getElementById("fileInput");
  if (!fileInput.files.length) {
    uploadStatusEl.textContent = "Choose a PDF first.";
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  uploadStatusEl.textContent = "Processing...";
  const res = await fetch("/upload", { method: "POST", body: formData });
  const data = await res.json();

  if (data.stem) {
    uploadStatusEl.textContent = `${data.filename} processed successfully.`;
    await loadDocuments();
  } else {
    uploadStatusEl.textContent = "Upload failed.";
  }
});

document.getElementById("askBtn").addEventListener("click", async () => {
  const question = document.getElementById("questionInput").value.trim();
  if (!question) return;

  const mode = document.querySelector('input[name="mode"]:checked').value;
  const selectedStems = Object.keys(knownDocs).filter(s => knownDocs[s].selected);

  answerBoxEl.textContent = "Searching...";
  sourcesBoxEl.innerHTML = "";

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

  sourcesBoxEl.innerHTML = "<h3>Retrieved Sources</h3>";
  (data.sources || []).forEach((src, i) => {
    const div = document.createElement("div");
    div.className = "source-item";
    div.innerHTML = `<strong>Source ${i + 1} — ${src.filename || "—"}, Pages: ${src.pages || "—"}</strong><p>${src.preview || ""}</p>`;
    sourcesBoxEl.appendChild(div);
  });
});

loadDocuments();