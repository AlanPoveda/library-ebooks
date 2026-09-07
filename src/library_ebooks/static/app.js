// Drag-and-drop de PDF (#22) + seleção de idioma/formato (#23) + envio
// pro /convert com polling de progresso via /progress/{job_id} (#25) +
// links de download dos arquivos gerados (#24). Mensagens dinâmicas
// usam TRANSLATIONS/getUiLang() de i18n.js (idioma da própria interface,
// carregado antes deste script).

function t() {
  return TRANSLATIONS[getUiLang()] || TRANSLATIONS[DEFAULT_UI_LANG];
}

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const browseButton = document.getElementById("browse-button");
const selectedFileLabel = document.getElementById("selected-file");
const optionsForm = document.getElementById("options-form");
const bookLangSelect = document.getElementById("book-lang");
const translateToSelect = document.getElementById("translate-to");
const generateAzw3Checkbox = document.getElementById("generate-azw3");
const checkGrammarCheckbox = document.getElementById("check-grammar");
const progressEl = document.getElementById("progress");
const resultDiv = document.getElementById("result");

function showSelectedFile(file) {
  if (file) {
    selectedFileLabel.textContent = `${t().selectedFilePrefix}: ${file.name}`;
  }
}

function setResult({ text, html, isError }) {
  resultDiv.classList.toggle("result--error", Boolean(isError));
  if (html) {
    resultDiv.innerHTML = html;
  } else {
    resultDiv.textContent = text || "";
  }
}

browseButton.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", () => {
  showSelectedFile(fileInput.files[0]);
});

dropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("dragover");
});

dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropzone.classList.remove("dragover");
  const file = event.dataTransfer.files[0];
  if (file) {
    fileInput.files = event.dataTransfer.files;
    showSelectedFile(file);
  }
});

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function pollProgress(jobId) {
  while (true) {
    const response = await fetch(`/progress/${jobId}`);
    const data = await response.json();

    if (!data.done) {
      progressEl.textContent = t().steps[data.step] || data.step;
      await sleep(500);
      continue;
    }

    progressEl.textContent = "";

    if (data.step === "error") {
      setResult({ text: `${t().errorPrefix}: ${data.detail}`, isError: true });
      return;
    }

    let html = `✓ ${t().conversionDone}: <a href="${data.epub_url}" download>${data.epub}</a>`;
    if (data.azw3_url) {
      html += ` ${t().and} <a href="${data.azw3_url}" download>${data.azw3}</a>`;
    }
    setResult({ html });
    return;
  }
}

optionsForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const file = fileInput.files[0];
  if (!file) {
    setResult({ text: t().selectPdfFirst, isError: true });
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  if (bookLangSelect.value) {
    formData.append("book_lang", bookLangSelect.value);
  }
  if (translateToSelect.value) {
    formData.append("translate_to", translateToSelect.value);
  }
  formData.append("generate_azw3", generateAzw3Checkbox.checked);
  formData.append("check_grammar", checkGrammarCheckbox.checked);

  setResult({ text: "" });
  progressEl.textContent = t().sending;

  try {
    const response = await fetch("/convert", { method: "POST", body: formData });
    const data = await response.json();

    if (!response.ok) {
      progressEl.textContent = "";
      setResult({ text: `${t().errorPrefix}: ${data.detail}`, isError: true });
      return;
    }

    await pollProgress(data.job_id);
  } catch (error) {
    progressEl.textContent = "";
    setResult({ text: `${t().errorPrefix}: ${error.message}`, isError: true });
  }
});
