#!/bin/bash
# Starts "Check the month". If Python is not on this Mac yet, it is installed first, once:
# that is the only moment anything is downloaded.
cd "$(dirname "$0")"

# 1. Python with its window toolkit already here?
PY=""
for c in /Library/Frameworks/Python.framework/Versions/3.*/bin/python3 /opt/homebrew/bin/python3 /usr/local/bin/python3; do
  if [ -x "$c" ] && "$c" -c "import tkinter" 2>/dev/null; then PY="$c"; fi
done

# 2. Not here: install it from python.org, once
if [ -z "$PY" ]; then
  echo
  echo " Python is not on this Mac yet. Downloading it from python.org (about 45 MB, once)."
  echo " Nothing else is installed, and nothing is sent anywhere."
  echo
  curl -L --fail -o /tmp/python-setup.pkg "https://www.python.org/ftp/python/3.12.7/python-3.12.7-macos11.pkg" || exit 1
  echo " The Mac will now ask for your password to install it."
  sudo installer -pkg /tmp/python-setup.pkg -target /
  PY=/Library/Frameworks/Python.framework/Versions/3.12/bin/python3
fi

# 3. Start the program
"$PY" check_month.pyw
