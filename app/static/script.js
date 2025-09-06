const form = document.getElementById("email-form");
const results = document.getElementById("results");
const categoryEl = document.getElementById("category");
const replyEl = document.getElementById("reply");
const copyBtn = document.getElementById("copy-btn");

// Alerts
const alertBox = document.getElementById("alert");
const alertText = document.getElementById("alert-text");
const alertClose = document.getElementById("alert-close");

function showError(msg) {
  alertText.textContent = msg;
  alertBox.classList.remove("hidden");
}

function hideAlert() {
  alertBox.classList.add("hidden");
  alertText.textContent = "";
}

alertClose.addEventListener("click", hideAlert);

// Custom file upload
const fileInput = document.getElementById("file");
const fileBtn = document.getElementById("file-btn");
const fileName = document.getElementById("file-name");
const dropzone = document.getElementById("dropzone");

function setFileName(name) {
  fileName.textContent = name || "Nenhum arquivo selecionado";
}

fileBtn.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("click", (e) => {
  // avoid triggering when clicking the close button etc.
  if (e.target === dropzone || e.target === fileName) fileInput.click();
});

fileInput.addEventListener("change", () => {
  setFileName(fileInput.files[0]?.name || "");
});

// Drag & Drop
["dragenter", "dragover"].forEach((evt) => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.add("dragover");
  });
});

["dragleave", "drop"].forEach((evt) => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove("dragover");
  });
});

dropzone.addEventListener("drop", (e) => {
  const dt = e.dataTransfer;
  const f = dt?.files?.[0];
  if (!f) return;
  const ok = /\.pdf$|\.txt$/i.test(f.name);
  if (!ok) {
    showError("Formato inválido. Use .txt ou .pdf.");
    return;
  }
  fileInput.files = dt.files;
  setFileName(f.name);
});

dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    fileInput.click();
  }
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const submit = document.getElementById("submit");
  submit.disabled = true;
  submit.textContent = "Processando...";

  hideAlert();

  const fd = new FormData();
  const file = fileInput.files[0];
  const text = document.getElementById("text").value.trim();
  if (file) fd.append("file", file);
  if (text) fd.append("text", text);

  if (!file && !text) {
    showError("Envie um arquivo ou cole o texto do email.");
    submit.disabled = false;
    submit.textContent = "Processar";
    return;
  }

  try {
    const res = await fetch("/api/process", {
      method: "POST",
      body: fd,
    });
    const data = await res.json();

    if (!res.ok) {
      showError(data.error || "Erro ao processar email.");
    } else {
      categoryEl.textContent = data.category;
      replyEl.value = data.reply;
      results.classList.remove("hidden");
      results.scrollIntoView({ behavior: "smooth" });
    }
  } catch (err) {
    showError("Falha na requisição: " + err.message);
  } finally {
    submit.disabled = false;
    submit.textContent = "Processar";
  }
});

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(replyEl.value);
    copyBtn.textContent = "Copiado!";
    setTimeout(() => (copyBtn.textContent = "Copiar resposta"), 1200);
  } catch (_) {
    showError("Não foi possível copiar.");
  }
});
