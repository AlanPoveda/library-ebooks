# library-ebooks

Converte PDFs em EPUB/AZW3 para Kindle e XTEINK, corrigindo hifenização
quebrada e traduzindo o livro (opcional) para espanhol, inglês ou
português. Veja `PLANNING.md` para a arquitetura completa.

## Setup

Dependências de sistema (macOS):

```bash
brew install enchant   # dicionários usados na correção de hifenização
```

O [Calibre](https://calibre-ebook.com/) precisa estar instalado
(`/Applications/calibre.app`) — é o motor de conversão PDF↔EPUB↔AZW3.

Ambiente Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Rodar os testes

```bash
pytest
```

## Rodar o app

```bash
uvicorn library_ebooks.app:app --reload
```

Por enquanto só existe a rota `POST /convert` (upload de PDF, sem
interface ainda — vem nas próximas histórias do épico App Web).
