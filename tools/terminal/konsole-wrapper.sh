#!/bin/bash
if [ "$1" = "--help" ] || [ "$1" = "-h" ] || [ "$1" = "--version" ]; then
    exec /usr/bin/konsole "$@"
fi

for cmd in qdbus wmctrl; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Warning: $cmd not found. Install it for full tab-reuse support." >&2
        exec /usr/bin/konsole "$@"
    fi
done

SERVICE=$(qdbus | grep -E '^ org\.kde\.konsole' | head -n1 | tr -d ' ')

if [ -n "$SERVICE" ]; then
    WIN_OBJ=$(qdbus "$SERVICE" /Windows 2>/dev/null | grep '/Windows/' | head -n1)
    if [ -z "$WIN_OBJ" ]; then
        WIN_OBJ="/Windows/1"
    fi
    qdbus "$SERVICE" "$WIN_OBJ" org.kde.konsole.Window.newSession >/dev/null 2>&1
    
    WID=$(wmctrl -l | grep -i konsole | head -n1 | awk '{print $1}')
    if [ -n "$WID" ]; then
        wmctrl -i -a "$WID" >/dev/null 2>&1
    fi
else
    /usr/bin/konsole --new-tab "$@" &
fi
