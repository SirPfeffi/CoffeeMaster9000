#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/coffeemaster9000"
APP_USER="pi"
PYTHON_BIN="/usr/bin/python3"
VENV_DIR="${APP_DIR}/.venv"

if [[ $EUID -ne 0 ]]; then
  echo "Run as root: sudo bash deploy/install_pi.sh"
  exit 1
fi

apt-get update
apt-get install -y python3 python3-venv python3-pip sqlite3 git

mkdir -p "${APP_DIR}"
cp -r . "${APP_DIR}"
chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

sudo -u "${APP_USER}" "${PYTHON_BIN}" -m venv "${VENV_DIR}"
sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install --upgrade pip
sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements.txt"

install -m 0644 "${APP_DIR}/deploy/coffeemaster-kiosk.service" /etc/systemd/system/coffeemaster-kiosk.service
install -m 0644 "${APP_DIR}/deploy/coffeemaster-web.service" /etc/systemd/system/coffeemaster-web.service
install -m 0644 "${APP_DIR}/deploy/coffeemaster-backup.service" /etc/systemd/system/coffeemaster-backup.service
install -m 0644 "${APP_DIR}/deploy/coffeemaster-backup.timer" /etc/systemd/system/coffeemaster-backup.timer
if [[ ! -f /etc/default/coffeemaster9000 ]]; then
  install -m 0644 "${APP_DIR}/deploy/coffeemaster.env.example" /etc/default/coffeemaster9000
fi

systemctl daemon-reload
systemctl enable coffeemaster-kiosk.service
systemctl enable coffeemaster-web.service
systemctl enable coffeemaster-backup.timer
systemctl restart coffeemaster-kiosk.service
systemctl restart coffeemaster-web.service
systemctl restart coffeemaster-backup.timer

echo "Installation complete."
