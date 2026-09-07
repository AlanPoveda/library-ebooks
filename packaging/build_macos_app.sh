#!/bin/bash
# Gera "Library Transformer.app": um app do macOS que sobe o servidor
# local e abre o navegador — pra não precisar usar o terminal no dia a
# dia. Por padrão instala na Área de Trabalho.
#
# Uso:
#   ./packaging/build_macos_app.sh                # -> ~/Desktop/Library Transformer.app
#   ./packaging/build_macos_app.sh /caminho/App.app
#
# Variável de ambiente opcional:
#   LIBRARY_TRANSFORMER_PORT=9000 ./packaging/build_macos_app.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_NAME="Library Transformer"
DEST="${1:-$HOME/Desktop/$APP_NAME.app}"
PORT="${LIBRARY_TRANSFORMER_PORT:-8800}"

if [ ! -d "$PROJECT_DIR/.venv" ]; then
  echo "Aviso: não achei $PROJECT_DIR/.venv — rode a instalação do README antes." >&2
fi

rm -rf "$DEST"
mkdir -p "$DEST/Contents/MacOS" "$DEST/Contents/Resources"

cp "$SCRIPT_DIR/AppIcon.icns" "$DEST/Contents/Resources/AppIcon.icns"

sed "s#__APP_NAME__#$APP_NAME#g" "$SCRIPT_DIR/Info.plist.template" > "$DEST/Contents/Info.plist"

sed -e "s#__PROJECT_DIR__#$PROJECT_DIR#g" -e "s#__PORT__#$PORT#g" \
  "$SCRIPT_DIR/launcher.sh.template" > "$DEST/Contents/MacOS/launcher"
chmod +x "$DEST/Contents/MacOS/launcher"

echo "Criado: $DEST"
echo "Dê dois cliques nele pra subir o servidor e abrir o app no navegador."
echo "(No primeiro clique o macOS pode avisar que é de 'desenvolvedor não identificado' —"
echo " clique com o botão direito > Abrir, uma vez só, pra liberar.)"
