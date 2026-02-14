#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

APP_DIR="${APP_DIR:-${SOURCE_DIR}}"
APP_USER="${APP_USER:-coffeemaster}"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
VENV_DIR="${APP_DIR}/.venv"
ENV_FILE="/etc/default/coffeemaster9000"

if [[ $EUID -ne 0 ]]; then
  echo "Run as root: sudo bash deploy/install_pi.sh"
  exit 1
fi

if [[ ! -f "${SOURCE_DIR}/requirements.txt" || ! -d "${SOURCE_DIR}/src" || ! -d "${SOURCE_DIR}/deploy" ]]; then
  echo "Could not detect CoffeeMaster9000 repository root at: ${SOURCE_DIR}"
  exit 1
fi

echo "Installing CoffeeMaster9000"
echo "SOURCE_DIR=${SOURCE_DIR}"
echo "APP_DIR=${APP_DIR}"
echo "APP_USER=${APP_USER}"

apt-get update
apt-get install -y python3 python3-dev python3-venv python3-pip build-essential sqlite3 git

if ! id -u "${APP_USER}" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "${APP_USER}"
fi
for grp in spi gpio input video render; do
  if getent group "${grp}" >/dev/null 2>&1; then
    usermod -aG "${grp}" "${APP_USER}"
  fi
done

# Ensure autologin for dedicated kiosk user (desktop and tty fallback).
if [[ -d /etc/lightdm/lightdm.conf.d || -f /etc/lightdm/lightdm.conf ]]; then
  mkdir -p /etc/lightdm/lightdm.conf.d
  cat > /etc/lightdm/lightdm.conf.d/50-coffeemaster-autologin.conf <<EOF
[Seat:*]
autologin-user=${APP_USER}
autologin-user-timeout=0
EOF

  if [[ -f /etc/lightdm/lightdm.conf ]]; then
    if grep -q '^autologin-user=' /etc/lightdm/lightdm.conf; then
      sed -i "s/^autologin-user=.*/autologin-user=${APP_USER}/" /etc/lightdm/lightdm.conf
    fi
    if grep -q '^autologin-user-timeout=' /etc/lightdm/lightdm.conf; then
      sed -i "s/^autologin-user-timeout=.*/autologin-user-timeout=0/" /etc/lightdm/lightdm.conf
    fi
    if ! grep -q '^autologin-user=' /etc/lightdm/lightdm.conf; then
      cat >> /etc/lightdm/lightdm.conf <<EOF

[Seat:*]
autologin-user=${APP_USER}
autologin-user-timeout=0
EOF
    fi
  fi
fi

mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/autologin.conf <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin ${APP_USER} --noclear %I \$TERM
EOF

# Optionally deploy to another directory (e.g. APP_DIR=/opt/coffeemaster9000).
if [[ "${APP_DIR}" != "${SOURCE_DIR}" ]]; then
  mkdir -p "${APP_DIR}"
  cp -a "${SOURCE_DIR}/." "${APP_DIR}/"
fi

chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

sudo -u "${APP_USER}" "${PYTHON_BIN}" -m venv "${VENV_DIR}"
sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install --upgrade pip
sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements.txt"

cat > /etc/systemd/system/coffeemaster-kiosk.service <<EOF
[Unit]
Description=CoffeeMaster9000 Kiosk App
After=network.target

[Service]
Type=simple
User=${APP_USER}
WorkingDirectory=${APP_DIR}/src
Environment=PYTHONPATH=${APP_DIR}/src
EnvironmentFile=-${ENV_FILE}
ExecStart=${APP_DIR}/.venv/bin/python ${APP_DIR}/src/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/coffeemaster-web.service <<EOF
[Unit]
Description=CoffeeMaster9000 Web App
After=network.target

[Service]
Type=simple
User=${APP_USER}
WorkingDirectory=${APP_DIR}/src
Environment=PYTHONPATH=${APP_DIR}/src
EnvironmentFile=-${ENV_FILE}
ExecStart=${APP_DIR}/.venv/bin/python ${APP_DIR}/src/webapp/app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/coffeemaster-backup.service <<EOF
[Unit]
Description=CoffeeMaster9000 Daily Backup
After=network.target

[Service]
Type=oneshot
User=${APP_USER}
WorkingDirectory=${APP_DIR}/src
Environment=PYTHONPATH=${APP_DIR}/src
EnvironmentFile=-${ENV_FILE}
ExecStart=${APP_DIR}/.venv/bin/python ${APP_DIR}/src/scripts/daily_backup.py
EOF

install -m 0644 "${APP_DIR}/deploy/coffeemaster-backup.timer" /etc/systemd/system/coffeemaster-backup.timer

if [[ ! -f "${ENV_FILE}" ]]; then
  sed "s|^COFFEEMASTER_DB_PATH=.*|COFFEEMASTER_DB_PATH=${APP_DIR}/src/data/coffee.db|" \
    "${APP_DIR}/deploy/coffeemaster.env.example" > "${ENV_FILE}"
  chmod 0644 "${ENV_FILE}"
elif grep -q '^COFFEEMASTER_DB_PATH=' "${ENV_FILE}"; then
  sed -i "s|^COFFEEMASTER_DB_PATH=.*|COFFEEMASTER_DB_PATH=${APP_DIR}/src/data/coffee.db|" "${ENV_FILE}"
else
  echo "COFFEEMASTER_DB_PATH=${APP_DIR}/src/data/coffee.db" >> "${ENV_FILE}"
fi

systemctl daemon-reload
systemctl enable coffeemaster-kiosk.service
systemctl enable coffeemaster-web.service
systemctl enable coffeemaster-backup.timer
systemctl restart coffeemaster-kiosk.service
systemctl restart coffeemaster-web.service
systemctl restart coffeemaster-backup.timer

echo "Installation complete. APP_DIR=${APP_DIR}"
