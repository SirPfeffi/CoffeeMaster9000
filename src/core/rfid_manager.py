import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

class RFIDManager:
    def __init__(self, spi_bus=0, spi_device=0):
        self.reader = SimpleMFRC522()
        self.callback = None

    def set_callback(self, func):
        self.callback = func

    def check_for_card(self):
        try:
            id, text = self.reader.read_no_block()
            if id and self.callback:
                self.callback(str(id))
        except Exception:
            pass
