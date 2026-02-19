# Installation (Raspberry Pi 4, latest Raspberry Pi OS)

This guide assumes:
- Raspberry Pi 4
- latest Raspberry Pi OS
- RFID reader (MFRC522/RC522) and Jura WE8 not attached yet

## 1. Prepare and update OS

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

## 2. Enable SPI (required for MFRC522)

```bash
sudo raspi-config
```

Then: `Interface Options` -> `SPI` -> `Enable`.

Optional check after reboot:

```bash
ls -l /dev/spidev0.0 /dev/spidev0.1
```

## 3. Clone project and run installer

```bash
git clone <YOUR_REPO_URL> CoffeeMaster9000
cd CoffeeMaster9000
chmod +x deploy/install_pi.sh
sudo bash deploy/install_pi.sh
```

The installer uses the dedicated Linux user `coffeemaster` for services and creates it automatically if missing.
It also configures autologin for `coffeemaster`:
- LightDM snippet: `/etc/lightdm/lightdm.conf.d/50-coffeemaster-autologin.conf`
- tty autologin is disabled by default; enable only if needed via `ENABLE_TTY_AUTOLOGIN=1`
- kiosk service is bound to graphical startup (`graphical.target`)
- Default install path is the current repository directory (for example `/home/coffeemaster/Coffeemaster9000`).
- Optional: install to a different path via `sudo APP_DIR=/opt/coffeemaster9000 bash deploy/install_pi.sh`.

## 4. Configure runtime environment

Edit:

```bash
sudo nano /etc/default/coffeemaster9000
```

Minimum recommended values:

```env
KAFFEEKASSE_SECRET=<long-random-secret>
COFFEEMASTER_GUI_LANG=de
COFFEEMASTER_WE8_ENABLED=0
```

For first admin bootstrap (one-time):

```env
COFFEEMASTER_BOOTSTRAP_ADMIN=admin
COFFEEMASTER_BOOTSTRAP_PASSWORD=<strong-password>
```

## 5. RFID wiring (MFRC522 / RC522)

Current code uses `SimpleMFRC522` defaults (SPI + standard reset pin), so wire as:

- RC522 `3.3V` -> Pi `3.3V` (Pin 1)
- RC522 `GND` -> Pi `GND` (Pin 6)
- RC522 `SDA` / `SS` -> Pi `CE0` GPIO8 (Pin 24)
- RC522 `SCK` -> Pi `SCLK` GPIO11 (Pin 23)
- RC522 `MOSI` -> Pi `MOSI` GPIO10 (Pin 19)
- RC522 `MISO` -> Pi `MISO` GPIO9 (Pin 21)
- RC522 `RST` -> Pi `GPIO25` (Pin 22)
- RC522 `IRQ` -> not used (leave unconnected)

Important:
- Use **3.3V only** for RC522 (do not use 5V).

After wiring, restart kiosk service and check logs:

```bash
sudo systemctl restart coffeemaster-kiosk.service
journalctl -u coffeemaster-kiosk.service -n 100 --no-pager
```

Expected:
- `RFID hardware detected` when reader is working.
- If not wired, app continues in simulation mode.

## 6. Possible WE8 interface (current implementation)

Current implementation supports:
- optional WE8 integration by network reachability (`host:port`)
- optional simulation mode for testing
- non-blocking behavior (core booking still works if WE8 is unavailable)

It does **not** yet implement full WE8 protocol parsing or direct auto-booking from machine events.

### 6.1 Network setup

- Connect Pi and WE8-related network endpoint to same LAN.
- Ensure WE8 endpoint IP/hostname is reachable from Pi.

### 6.2 Configuration

In `/etc/default/coffeemaster9000`:

```env
COFFEEMASTER_WE8_ENABLED=1
COFFEEMASTER_WE8_HOST=<we8-endpoint-ip-or-hostname>
COFFEEMASTER_WE8_PORT=80
COFFEEMASTER_WE8_TIMEOUT_SECONDS=2.0
COFFEEMASTER_WE8_SIMULATE=0
```

For dry-run without hardware:

```env
COFFEEMASTER_WE8_ENABLED=1
COFFEEMASTER_WE8_SIMULATE=1
```

Apply changes:

```bash
sudo systemctl restart coffeemaster-kiosk.service
sudo systemctl restart coffeemaster-web.service
```

Then open web UI:
- `http://<raspi-ip>:5000/integrations`

## 7. Backup setup (USB + optional SMB)

Backup implementation in this project:
- scheduler: `systemd` timer (`coffeemaster-backup.timer`) once daily
- executor: `coffeemaster-backup.service` -> `src/scripts/daily_backup.py`
- targets:
  - USB path from `COFFEEMASTER_USB_BACKUP_PATH` (default `/media/usb`)
  - optional network path from `COFFEEMASTER_NETWORK_BACKUP_PATH`
- filename format: `kaffeekasse_backup_YYYYMMDD_HHMMSS.db`

### 7.1 Configure backup paths

Edit:

```bash
sudo nano /etc/default/coffeemaster9000
```

Set at least:

```env
COFFEEMASTER_DB_PATH=/home/coffeemaster/Coffeemaster9000/src/data/coffee.db
COFFEEMASTER_USB_BACKUP_PATH=/media/usb
COFFEEMASTER_BACKUP_MAX_RETRIES=10
```

Optional SMB target:

```env
COFFEEMASTER_NETWORK_BACKUP_PATH=/mnt/smb/coffeemaster
```

### 7.2 USB backup mount example

Create mountpoint:

```bash
sudo mkdir -p /media/usb
```

Find USB device and filesystem UUID:

```bash
lsblk -f
```

Add to `/etc/fstab` (example):

```fstab
UUID=<USB_UUID>  /media/usb  ext4  defaults,nofail,x-systemd.device-timeout=10  0  2
```

Then:

```bash
sudo mount -a
ls -la /media/usb
```

### 7.3 Optional SMB mount example

Install CIFS tools:

```bash
sudo apt install -y cifs-utils
```

Create mountpoint + credentials file:

```bash
sudo mkdir -p /mnt/smb/coffeemaster
sudo nano /etc/samba/creds-coffeemaster
```

Credentials file content:

```txt
username=<smb_user>
password=<smb_password>
domain=<optional_domain>
```

Protect it:

```bash
sudo chmod 600 /etc/samba/creds-coffeemaster
```

Add to `/etc/fstab` (example):

```fstab
//<server>/<share>  /mnt/smb/coffeemaster  cifs  credentials=/etc/samba/creds-coffeemaster,uid=coffeemaster,gid=coffeemaster,file_mode=0660,dir_mode=0770,iocharset=utf8,nofail,x-systemd.automount  0  0
```

Then:

```bash
sudo mount -a
ls -la /mnt/smb/coffeemaster
```

### 7.4 Scheduler: systemd timer vs cron

Current installation uses `systemd` timer:
- `coffeemaster-backup.timer` (`OnCalendar=daily`)
- `coffeemaster-backup.service`

Legacy file `src/scripts/cronjob-settings.txt` is only reference material and is not installed automatically.

### 7.5 Backup verification

Run manual backup job:

```bash
sudo systemctl start coffeemaster-backup.service
```

Check timer and last runs:

```bash
systemctl status coffeemaster-backup.timer --no-pager
journalctl -u coffeemaster-backup.service -n 100 --no-pager
```

Check files:

```bash
ls -lah /media/usb | grep kaffeekasse_backup_ || true
ls -lah /mnt/smb/coffeemaster | grep kaffeekasse_backup_ || true
```

## 8. Start and enable services

```bash
sudo systemctl daemon-reload
sudo systemctl restart coffeemaster-kiosk.service
sudo systemctl restart coffeemaster-web.service
sudo systemctl restart coffeemaster-backup.timer
```

## 9. Verify service health

```bash
systemctl status coffeemaster-kiosk.service --no-pager
systemctl status coffeemaster-web.service --no-pager
systemctl status coffeemaster-backup.timer --no-pager
```

## 10. Access web interface

- Open: `http://<raspi-ip>:5000`
- Without RFID hardware attached, kiosk runs in simulation mode and UID can be typed manually.

## 11. Debugging logs

```bash
journalctl -u coffeemaster-kiosk.service -f
journalctl -u coffeemaster-web.service -f
journalctl -u coffeemaster-backup.service -f
```
