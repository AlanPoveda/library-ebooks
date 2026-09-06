// Drag-and-drop de PDF (história #22). A seleção/idioma/formato de
// saída e o envio pro /convert entram nas próximas histórias.

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const browseButton = document.getElementById("browse-button");
const selectedFileLabel = document.getElementById("selected-file");

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
