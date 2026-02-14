#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/coffeemaster9000"
APP_USER="coffeemaster"
PYTHON_BIN="/usr/bin/python3"
VENV_DIR="${APP_DIR}/.venv"

if [[ $EUID -ne 0 ]]; then
  echo "Run as root: sudo bash deploy/install_pi.sh"
  exit 1
fi

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
