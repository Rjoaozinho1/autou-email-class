const form = document.getElementById("email-form");
const results = document.getElementById("results");
const categoryEl = document.getElementById("category");
const replyEl = document.getElementById("reply");
const copyBtn = document.getElementById("copy-btn");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const submit = document.getElementById("submit");
  submit.disabled = true;
  submit.textContent = "Processando...";

  const fd = new FormData();
  const file = document.getElementById("file").files[0];
  const text = document.getElementById("text").value.trim();
  if (file) fd.append("file", file);
  if (text) fd.append("text", text);

  try {
    const res = await fetch("/api/process", {
      method: "POST",
      body: fd,
    });
    const data = await res.json();

    if (!res.ok) {
      alert(data.error || "Erro ao processar.");
    } else {
      categoryEl.textContent = data.category;
      replyEl.value = data.reply;
      results.classList.remove("hidden");
      results.scrollIntoView({ behavior: "smooth" });
    }
  } catch (err) {
    alert("Falha na requisição: " + err.message);
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
    alert("Não foi possível copiar.");
  }
});
