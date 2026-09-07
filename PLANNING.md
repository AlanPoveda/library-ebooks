# PLANNING.md

## Objetivo

App web local (drag-and-drop) para converter PDFs em EPUB, corrigindo a
hifenização quebrada que vem da extração de PDF, revisando gramática e,
opcionalmente, traduzindo o livro inteiro para espanhol, inglês ou
português.

**Escopo do app**: converter → traduzir (opcional) → revisar gramática
(opcional) → disponibilizar para download. O app não se responsabiliza por
levar o arquivo até o Kindle/XTEINK — isso fica a critério do usuário
(email, cabo, Send-to-Kindle etc.). EPUB é o formato principal de saída;
AZW3 é oferecido como **opção adicional no momento do download**, gerado
via Calibre quando disponível, mas não é o foco do app.

## Decisões de arquitetura

| Decisão | Escolha | Motivo |
|---|---|---|
| Tipo de app | Web app local (FastAPI + frontend simples no navegador) | Mais rápido de construir e testar que um app desktop nativo; UX de arrastar arquivo funciona igual num navegador |
| Motor de conversão PDF→EPUB | Calibre (`ebook-convert`, chamado via subprocess) | Usuário já usa Calibre pra biblioteca; é o motor mais robusto disponível |
| Formato AZW3 | Opcional, gerado via Calibre só se o usuário escolher no download | App não assume responsabilidade de "chegar" no Kindle — isso é decisão do usuário |
| Motor de tradução | Argos Translate (offline) | Grátis, roda local, sem enviar o conteúdo do livro pra fora |
| Correção de hifenização | Módulo próprio (regex + validação por dicionário) | Não existe lib pronta boa pra isso, principalmente em PT-BR |
| Verificação gramatical/estilo | LanguageTool local (`language-tool-python`) | Padrão open-source pra lint gramatical (concordância, crase, pontuação); roda servidor local, texto não sai da máquina |

## Pipeline

```
PDF (upload/drag)
  │
  ▼
[1] ebook-convert pdf → epub_bruto        (Calibre)
  │
  ▼
[2] dehyphenate(epub_bruto) → epub_limpo  (regex + dicionário pt/es/en)
  │
  ▼
[3] lint_gramatical(epub_limpo)?          (LanguageTool local, opcional)
  │
  ▼
[4] translate(epub_corrigido, idioma)?    (Argos Translate, opcional)
  │
  ▼
[5] ebook-convert epub_final → azw3       (Calibre)
  │
  ▼
Download: EPUB + AZW3
```

O lint gramatical (etapa [3]) reporta problemas por capítulo e pode
corrigir automaticamente apenas sugestões de alta confiança — o resto
fica só no relatório.

## Estrutura do repositório

```
library-ebooks/
├── CLAUDE.md
├── PLANNING.md
├── pyproject.toml
├── src/
│   └── library_ebooks/
│       ├── convert.py       # wrapper do Calibre (ebook-convert)
│       ├── dehyphenate.py   # limpeza de hifenização
│       ├── translate.py     # backend Argos Translate
│       ├── lint.py          # verificação gramatical via LanguageTool local
│       ├── pipeline.py      # orquestra as etapas acima
│       ├── app.py           # FastAPI: rotas de upload/download
│       └── static/          # HTML/JS da área de drag-and-drop
├── tests/
│   ├── fixtures/            # PDFs/EPUBs pequenos de teste
│   ├── test_dehyphenate.py
│   ├── test_convert.py
│   ├── test_translate.py
│   ├── test_lint.py
│   └── test_pipeline.py
└── books/                   # entrada/saída local (gitignored — não versionar ebooks)
```

## Riscos / pontos de atenção conhecidos

- **Dependência do Calibre**: o app assume `ebook-convert` disponível no
  PATH do usuário (já é o caso aqui). Se não estiver, falhar com mensagem
  clara em vez de erro obscuro.
- **Argos Translate e pares de idioma**: nem todo par (ex: pt→es) tem pacote
  direto — pode ser necessário traduzir em duas etapas (pt→en→es) quando o
  par direto não existir.
- **Tradução de livro inteiro é lenta (CPU-only, sem GPU)**: medido em
  produção com um livro real (~155 mil palavras, ~10.500 nós de texto):
  ~150ms por parágrafo de ~20 palavras, dando **~20-30 min pro livro
  inteiro**. Confirmado por medição direta que **não é overhead por
  chamada** — 30 chamadas separadas e 1 chamada com o mesmo conteúdo
  total levaram o mesmo tempo (4.55s vs 4.56s) — é tempo real de
  inferência do modelo, proporcional ao volume de texto. Agrupar por
  capítulo não ajudaria; só GPU ou um modelo menor reduziriam isso, o
  que é uma frente maior, fora de escopo por ora. UI não mostra
  progresso dentro da etapa "translate" (só o nome da etapa) — pode
  parecer travado num livro grande.
- **Dehyphenation**: precisa de dicionários (`pyenchant`/hunspell) para
  `pt_BR`, `es`, `en` para validar se a junção de duas linhas forma uma
  palavra real, evitando juntar hífens que são legítimos (ex: "guarda-chuva").
- **Não versionar livros**: PDFs/EPUBs reais vão em `books/`, que fica no
  `.gitignore` — só código e fixtures pequenas de teste são versionados.
- **Aspell tem cobertura fraca de compostos hifenizados em ES/EN**: o
  backend usado pelo `pyenchant` (aspell) reconhece bem palavras compostas
  com hífen em pt_BR (ex: "guarda-chuva", "micro-ondas"), mas praticamente
  não tem entradas assim em es/en (ex: "well-known", "político-militar"
  não são reconhecidos nem com nem sem hífen). Nesses casos o fallback
  ingênuo (juntar sem hífen) é usado — comportamento seguro, mas vale
  reavaliar o backend (hunspell?) se isso se mostrar um problema real com
  livros em es/en.
- **LanguageTool precisa de Java**: `language-tool-python` sobe um servidor
  LanguageTool local que roda sobre JRE — precisa checar/documentar essa
  dependência de sistema (assim como o Calibre), com erro claro se não
  encontrar Java instalado.

## Próximos passos (ordem sugerida de implementação em TDD)

1. `dehyphenate.py` — módulo isolado, fácil de testar com casos conhecidos.
2. `convert.py` — wrapper fino do `ebook-convert`, testado com PDF/EPUB de fixture.
3. `translate.py` — wrapper do Argos Translate, com fallback de pivô de idioma.
4. `lint.py` — wrapper do LanguageTool local, relatório + correções de alta confiança.
5. `pipeline.py` — junta as quatro etapas.
6. `app.py` + frontend — interface de drag-and-drop por cima do pipeline já testado.
