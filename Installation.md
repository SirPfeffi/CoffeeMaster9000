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

## 7. Start and enable services

```bash
sudo systemctl daemon-reload
sudo systemctl restart coffeemaster-kiosk.service
sudo systemctl restart coffeemaster-web.service
sudo systemctl restart coffeemaster-backup.timer
```

## 8. Verify service health

```bash
systemctl status coffeemaster-kiosk.service --no-pager
systemctl status coffeemaster-web.service --no-pager
systemctl status coffeemaster-backup.timer --no-pager
```

## 9. Access web interface

- Open: `http://<raspi-ip>:5000`
- Without RFID hardware attached, kiosk runs in simulation mode and UID can be typed manually.

## 10. Debugging logs

```bash
journalctl -u coffeemaster-kiosk.service -f
journalctl -u coffeemaster-web.service -f
journalctl -u coffeemaster-backup.service -f
```
