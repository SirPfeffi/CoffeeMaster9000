# Installation (Raspberry Pi 4, latest Raspberry Pi OS)

This guide assumes:
- Raspberry Pi 4
- latest Raspberry Pi OS
- RFID reader and Jura WE8 not attached yet

## 1. Prepare and update OS

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

## 2. Enable SPI (recommended now, required when RFID is attached)

```bash
sudo raspi-config
```

Then: `Interface Options` -> `SPI` -> `Enable`.

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

## 5. Start and enable services

```bash
sudo systemctl daemon-reload
sudo systemctl restart coffeemaster-kiosk.service
sudo systemctl restart coffeemaster-web.service
sudo systemctl restart coffeemaster-backup.timer
```

## 6. Verify service health

```bash
systemctl status coffeemaster-kiosk.service --no-pager
systemctl status coffeemaster-web.service --no-pager
systemctl status coffeemaster-backup.timer --no-pager
```

## 7. Access web interface

- Open: `http://<raspi-ip>:5000`
- Without RFID hardware attached, kiosk runs in simulation mode and UID can be typed manually.

## 8. Debugging logs

```bash
journalctl -u coffeemaster-kiosk.service -f
journalctl -u coffeemaster-web.service -f
journalctl -u coffeemaster-backup.service -f
```
