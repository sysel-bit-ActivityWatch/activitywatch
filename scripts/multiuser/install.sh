#!/usr/bin/env bash
# Install the already-built local bundle; requires root.
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_dir=$(cd -- "$script_dir/../.." && pwd)
bundle="$repo_dir/dist/activitywatch"
import_db=${1:-}
extension_source=${2:-}
if (( EUID != 0 )); then
    echo 'Run with sudo; see scripts/multiuser/README.md.' >&2
    exit 1
fi
for tool in python3 systemctl useradd getent install cp flock; do
    command -v "$tool" >/dev/null || { echo "Missing command: $tool" >&2; exit 1; }
done
[[ -x "$bundle/aw-server/aw-server" && -x "$bundle/aw-awatcher" ]] || {
    echo 'Build dist/activitywatch first.' >&2; exit 1;
}
if [[ -n $import_db && ! -f $import_db ]]; then
    echo "Database not found: $import_db" >&2; exit 1
fi
if [[ -n $extension_source && ! -f $extension_source/metadata.json ]]; then
    echo "GNOME extension not found: $extension_source" >&2; exit 1
fi
# Refuse to replace a running personal server or its database implicitly.
if python3 - <<'PY'
import socket
with socket.socket() as s:
    raise SystemExit(0 if s.connect_ex(('127.0.0.1', 5600)) == 0 else 1)
PY
then
    echo 'Port 5600 is in use. Quit ActivityWatch before installing.' >&2
    exit 1
fi
destination=/var/lib/activitywatch/data/activitywatch/aw-server/peewee-sqlite.v2.db
if [[ -n $import_db && -e $destination ]]; then
    echo 'Shared database already exists; refusing to overwrite it.' >&2; exit 1
fi
getent passwd activitywatch >/dev/null || useradd --system --user-group \
    --home-dir /var/lib/activitywatch --shell /usr/sbin/nologin activitywatch
install -d -m 755 /opt/activitywatch
cp -a --remove-destination "$bundle/." /opt/activitywatch/
chown -R root:root /opt/activitywatch
chmod -R a+rX /opt/activitywatch
install -m 755 "$script_dir/start-session-watcher" /opt/activitywatch/start-session-watcher
install -d -o activitywatch -g activitywatch -m 700 /var/lib/activitywatch
install -d -o activitywatch -g activitywatch -m 700 \
    /var/lib/activitywatch/data /var/lib/activitywatch/config /var/lib/activitywatch/cache \
    /var/lib/activitywatch/data/activitywatch /var/lib/activitywatch/data/activitywatch/aw-server
if [[ -n $import_db ]]; then
    destination=/var/lib/activitywatch/data/activitywatch/aw-server/peewee-sqlite.v2.db
    if [[ -e $destination ]]; then
        echo 'Shared database already exists; refusing to overwrite it.' >&2; exit 1
    fi
    # SQLite backup includes committed WAL data; the original remains untouched.
    python3 - "$import_db" "$destination" <<'PY'
import sqlite3
import sys
from pathlib import Path
with sqlite3.connect(Path(sys.argv[1]).resolve().as_uri() + '?mode=ro', uri=True) as source:
    with sqlite3.connect(sys.argv[2]) as target:
        source.backup(target)
PY
    chown activitywatch:activitywatch "$destination"
    chmod 600 "$destination"
fi
if [[ -n $extension_source ]]; then
    install -d -m 755 /usr/share/gnome-shell/extensions/focused-window-dbus@flexagoon.com
    cp -a "$extension_source/." /usr/share/gnome-shell/extensions/focused-window-dbus@flexagoon.com/
    chown -R root:root /usr/share/gnome-shell/extensions/focused-window-dbus@flexagoon.com
    chmod -R a+rX /usr/share/gnome-shell/extensions/focused-window-dbus@flexagoon.com
fi
install -m 644 "$script_dir/activitywatch-server.service" /etc/systemd/system/activitywatch-server.service
install -m 644 "$script_dir/activitywatch-session.desktop" /etc/xdg/autostart/activitywatch-session.desktop
systemctl daemon-reload
systemctl enable --now activitywatch-server.service
printf '%s\n' 'Installed. Log out and back in for each graphical user.' \
    'Open http://localhost:5600/ and select the user in Activity.'
