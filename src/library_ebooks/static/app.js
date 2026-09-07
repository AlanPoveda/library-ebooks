// Drag-and-drop de PDF (#22) + seleção de idioma/formato (#23) + envio
// pro /convert com polling de progresso via /progress/{job_id} (#25) +
// links de download dos arquivos gerados (#24).

const STEP_LABELS = {
  queued: "Na fila...",
  pdf_to_epub: "Convertendo PDF para EPUB...",
  dehyphenate: "Corrigindo hifenização...",
  grammar_check: "Verificando gramática...",
  translate: "Traduzindo...",
  epub_to_azw3: "Gerando AZW3...",
};

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
    selectedFileLabel.textContent = `Selecionado: ${file.name}`;
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
      progressEl.textContent = STEP_LABELS[data.step] || data.step;
      await sleep(500);
      continue;
    }

    progressEl.textContent = "";

    if (data.step === "error") {
      resultDiv.textContent = `Erro: ${data.detail}`;
      return;
    }

    let html = `Conversão concluída: <a href="${data.epub_url}" download>${data.epub}</a>`;
    if (data.azw3_url) {
      html += ` e <a href="${data.azw3_url}" download>${data.azw3}</a>`;
    }
    resultDiv.innerHTML = html;
    return;
  }
}

optionsForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const file = fileInput.files[0];
  if (!file) {
    resultDiv.textContent = "Selecione um PDF antes de converter.";
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

  resultDiv.textContent = "";
  progressEl.textContent = "Enviando...";

  try {
    const response = await fetch("/convert", { method: "POST", body: formData });
    const data = await response.json();

    if (!response.ok) {
      progressEl.textContent = "";
      resultDiv.textContent = `Erro: ${data.detail}`;
      return;
    }

    await pollProgress(data.job_id);
  } catch (error) {
    progressEl.textContent = "";
    resultDiv.textContent = `Erro: ${error.message}`;
  }
});
