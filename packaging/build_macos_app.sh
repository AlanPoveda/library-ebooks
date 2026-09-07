#!/bin/bash
# Gera dois apps do macOS pra não precisar de terminal no dia a dia:
#
#   "Library Transformer.app"       -> sobe o servidor e abre o navegador
#   "Stop Library Transformer.app"  -> para o servidor
#
# Por padrão instala os dois na Área de Trabalho.
#
# Uso:
#   ./packaging/build_macos_app.sh                # -> ~/Desktop
#   ./packaging/build_macos_app.sh /algum/dir      # -> dir escolhido
#
# Variável de ambiente opcional:
#   LIBRARY_TRANSFORMER_PORT=9000 ./packaging/build_macos_app.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DEST_DIR="${1:-$HOME/Desktop}"
PORT="${LIBRARY_TRANSFORMER_PORT:-8800}"

if [ ! -d "$PROJECT_DIR/.venv" ]; then
  echo "Aviso: não achei $PROJECT_DIR/.venv — rode a instalação do README antes." >&2
fi

build_app() {
  local app_name="$1" template="$2" icon="$3" dest="$DEST_DIR/$1.app"

  rm -rf "$dest"
  mkdir -p "$dest/Contents/MacOS" "$dest/Contents/Resources"

  cp "$SCRIPT_DIR/$icon.icns" "$dest/Contents/Resources/$icon.icns"

  sed -e "s#__APP_NAME__#$app_name#g" -e "s#__ICON_FILE__#$icon#g" \
    "$SCRIPT_DIR/Info.plist.template" > "$dest/Contents/Info.plist"

  sed -e "s#__PROJECT_DIR__#$PROJECT_DIR#g" -e "s#__PORT__#$PORT#g" \
    "$SCRIPT_DIR/$template" > "$dest/Contents/MacOS/launcher"
  chmod +x "$dest/Contents/MacOS/launcher"

  echo "Criado: $dest"
}

build_app "Library Transformer" "launcher.sh.template" "AppIcon"
build_app "Stop Library Transformer" "stop_launcher.sh.template" "StopIcon"

echo
echo "Dê dois cliques em 'Library Transformer' pra abrir, e em"
echo "'Stop Library Transformer' pra parar o servidor quando quiser."
echo "(No primeiro clique de cada um o macOS pode avisar que é de"
echo " 'desenvolvedor não identificado' — clique com o botão direito >"
echo " Abrir, uma vez só por app, pra liberar.)"
