import logging

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
    from mfrc522 import SimpleMFRC522
except Exception:
    GPIO = None
    SimpleMFRC522 = None
    logger.warning("RFID-Module nicht verfügbar. Läuft im Simulationsmodus.")

class RFIDManager:
    def __init__(self):
        if SimpleMFRC522:
            self.reader = SimpleMFRC522()
        else:
            self.reader = None
        self.callback = None

    def set_callback(self, func):
        self.callback = func

    def check_for_card(self):
        if not self.reader:
            return
        try:
            id, text = self.reader.read_no_block()
            if id and self.callback:
                self.callback(str(id))
        except Exception as e:
            logger.exception("Fehler beim Lesen der RFID-Karte: %s", e)