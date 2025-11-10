import logging

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
    from mfrc522 import SimpleMFRC522
    HARDWARE_AVAILABLE = True
except Exception:
    GPIO = None
    SimpleMFRC522 = None
    HARDWARE_AVAILABLE = False
    logger.warning("RFID-Module nicht verfügbar. Läuft im Simulationsmodus.")

class RFIDManager:
    def __init__(self):
        if SimpleMFRC522:
            try:
                self.reader = SimpleMFRC522()
            except Exception as e:
                logger.error("Fehler beim Initialisieren des RFID-Readers: %s", e)
                self.reader = None
        else:
            self.reader = None
        self.callback = None

    def is_hardware_available(self):
        """Prüft, ob RFID-Hardware verfügbar ist"""
        return HARDWARE_AVAILABLE and self.reader is not None

    def set_callback(self, func):
        """Setzt die Callback-Funktion für RFID-Scans"""
        self.callback = func

    def check_for_card(self):
        """Prüft auf RFID-Karten und ruft Callback auf"""
        if not self.reader:
            return
        try:
            id, text = self.reader.read_no_block()
            if id and self.callback:
                self.callback(str(id))
        except Exception as e:
            logger.exception("Fehler beim Lesen der RFID-Karte: %s", e)