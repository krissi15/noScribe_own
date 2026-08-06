#!/usr/bin/env bash
# Trägt Traudi ins Anwendungsmenü ein (Linux, nur für die eigene Anmeldung).
#
#   packaging/install-desktop-entry.sh [Pfad zur Traudi-Programmdatei]
#
# Ohne Argument wird `python -m noScribe` aus dem Projektverzeichnis
# eingetragen -- praktisch für die Entwicklung. Für eine gebaute Fassung den
# Pfad zur ausführbaren Datei aus pyinstaller/dist/ mitgeben.

set -euo pipefail
cd "$(dirname "$0")/.."
project_root="$(pwd)"

target="${1:-}"
if [ -z "$target" ]; then
    if [ -x venv/bin/python ]; then
        target="$project_root/venv/bin/python -m noScribe"
    else
        target="python3 -m noScribe"
    fi
fi

apps_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
icons_dir="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/256x256/apps"
mkdir -p "$apps_dir" "$icons_dir"

cp img/traudi_logo.png "$icons_dir/traudi.png"

# Exec muss ein absoluter Aufruf sein; %f reicht die angeklickte Datei durch.
sed "s|^Exec=.*|Exec=$target %f|" packaging/traudi.desktop \
    > "$apps_dir/traudi.desktop"
chmod 644 "$apps_dir/traudi.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$apps_dir" || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor" || true
fi

echo "Eingetragen: $apps_dir/traudi.desktop"
echo "Symbol:      $icons_dir/traudi.png"
