// Drag-and-drop de PDF (#22) + seleção de idioma/formato e envio pro
// /convert (#23). O endpoint de download dos arquivos gerados (#24)
// ainda não existe, então o resultado por enquanto é só texto.

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const browseButton = document.getElementById("browse-button");
const selectedFileLabel = document.getElementById("selected-file");
const optionsForm = document.getElementById("options-form");
const bookLangSelect = document.getElementById("book-lang");
const translateToSelect = document.getElementById("translate-to");
const generateAzw3Checkbox = document.getElementById("generate-azw3");
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

  resultDiv.textContent = "Convertendo...";

  try {
    const response = await fetch("/convert", { method: "POST", body: formData });
    const data = await response.json();

    if (!response.ok) {
      resultDiv.textContent = `Erro: ${data.detail}`;
      return;
    }

    resultDiv.textContent = data.azw3
      ? `Conversão concluída: ${data.epub} e ${data.azw3}`
      : `Conversão concluída: ${data.epub}`;
  } catch (error) {
    resultDiv.textContent = `Erro: ${error.message}`;
  }
});
