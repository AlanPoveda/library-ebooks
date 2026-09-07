// Tradução da própria interface do app (não confundir com "idioma do
// livro" / "traduzir para", que são sobre o conteúdo do PDF). Carregado
// antes do app.js, que reaproveita TRANSLATIONS/getUiLang() pras
// mensagens dinâmicas (progresso, sucesso, erro).

const DEFAULT_UI_LANG = "pt";

const TRANSLATIONS = {
  pt: {
    subtitle:
      "Converte PDF em EPUB, corrige hifenização, traduz e revisa gramática — tudo local, direto no seu computador.",
    dropzoneText: "Arraste um PDF aqui, ou",
    selectedFilePrefix: "Selecionado",
    browseButton: "escolha um arquivo",
    bookLangLabel: "Idioma do livro",
    bookLangHint: "usado pra corrigir hifenização quebrada",
    bookLangNone: "não corrigir por dicionário",
    translateToLabel: "Traduzir para",
    translateToHint: "um livro inteiro pode levar minutos",
    translateToNone: "não traduzir",
    optionPt: "Português",
    optionEs: "Espanhol",
    optionEn: "Inglês",
    generateAzw3Label: "Gerar também AZW3 (Kindle)",
    checkGrammarLabel: "Verificar e corrigir gramática",
    convertButton: "Converter",
    footer: "Roda 100% local — nenhum arquivo sai do seu computador.",
    selectPdfFirst: "Selecione um PDF antes de converter.",
    sending: "Enviando...",
    conversionDone: "Conversão concluída",
    and: "e",
    errorPrefix: "Erro",
    steps: {
      queued: "Na fila...",
      pdf_to_epub: "Convertendo PDF para EPUB...",
      dehyphenate: "Corrigindo hifenização...",
      grammar_check: "Verificando gramática...",
      translate: "Traduzindo...",
      epub_to_azw3: "Gerando AZW3...",
    },
  },
  en: {
    subtitle:
      "Converts PDF to EPUB, fixes broken hyphenation, translates, and checks grammar — all locally, on your own computer.",
    dropzoneText: "Drag a PDF here, or",
    selectedFilePrefix: "Selected",
    browseButton: "choose a file",
    bookLangLabel: "Book language",
    bookLangHint: "used to fix broken hyphenation",
    bookLangNone: "don't check dictionary",
    translateToLabel: "Translate to",
    translateToHint: "a whole book can take minutes",
    translateToNone: "don't translate",
    optionPt: "Portuguese",
    optionEs: "Spanish",
    optionEn: "English",
    generateAzw3Label: "Also generate AZW3 (Kindle)",
    checkGrammarLabel: "Check and fix grammar",
    convertButton: "Convert",
    footer: "Runs 100% locally — no file ever leaves your computer.",
    selectPdfFirst: "Select a PDF before converting.",
    sending: "Uploading...",
    conversionDone: "Conversion complete",
    and: "and",
    errorPrefix: "Error",
    steps: {
      queued: "Queued...",
      pdf_to_epub: "Converting PDF to EPUB...",
      dehyphenate: "Fixing hyphenation...",
      grammar_check: "Checking grammar...",
      translate: "Translating...",
      epub_to_azw3: "Generating AZW3...",
    },
  },
  es: {
    subtitle:
      "Convierte PDF a EPUB, corrige la separación silábica rota, traduce y revisa la gramática — todo localmente, en tu ordenador.",
    dropzoneText: "Arrastra un PDF aquí, o",
    selectedFilePrefix: "Seleccionado",
    browseButton: "elige un archivo",
    bookLangLabel: "Idioma del libro",
    bookLangHint: "se usa para corregir la separación silábica rota",
    bookLangNone: "no corregir con diccionario",
    translateToLabel: "Traducir a",
    translateToHint: "un libro completo puede tardar minutos",
    translateToNone: "no traducir",
    optionPt: "Portugués",
    optionEs: "Español",
    optionEn: "Inglés",
    generateAzw3Label: "Generar también AZW3 (Kindle)",
    checkGrammarLabel: "Verificar y corregir gramática",
    convertButton: "Convertir",
    footer: "Funciona 100% localmente — ningún archivo sale de tu ordenador.",
    selectPdfFirst: "Selecciona un PDF antes de convertir.",
    sending: "Enviando...",
    conversionDone: "Conversión completada",
    and: "y",
    errorPrefix: "Error",
    steps: {
      queued: "En cola...",
      pdf_to_epub: "Convirtiendo PDF a EPUB...",
      dehyphenate: "Corrigiendo separación silábica...",
      grammar_check: "Verificando gramática...",
      translate: "Traduciendo...",
      epub_to_azw3: "Generando AZW3...",
    },
  },
};

function getUiLang() {
  return localStorage.getItem("uiLang") || DEFAULT_UI_LANG;
}

function applyUiLang(lang) {
  const dict = TRANSLATIONS[lang] || TRANSLATIONS[DEFAULT_UI_LANG];

  document.documentElement.lang = lang === "pt" ? "pt-br" : lang;

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const value = dict[el.getAttribute("data-i18n")];
    if (typeof value === "string") {
      el.textContent = value;
    }
  });

  localStorage.setItem("uiLang", lang);
}

document.addEventListener("DOMContentLoaded", () => {
  const uiLangSelect = document.getElementById("ui-lang");
  const savedLang = getUiLang();
  uiLangSelect.value = savedLang;
  applyUiLang(savedLang);

  uiLangSelect.addEventListener("change", () => applyUiLang(uiLangSelect.value));
});
