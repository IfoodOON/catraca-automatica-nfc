"""Ponto de entrada da aplicação da catraca automatizada (LAB 220)."""

import logging
import queue

import config.settings as settings
from core.access_control import AccessControlFSM
from core.card_registry import CardRegistry
from gui.app import App
from hardware.nfc_reader import NfcReader
from hardware.serial_comm import SerialManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def main() -> None:
    fila_eventos: queue.Queue = queue.Queue()

    card_registry = CardRegistry(settings.CARTOES_FILE)

    serial_manager = SerialManager(
        fila_eventos=fila_eventos,
        baud_rate=settings.SERIAL_BAUD_RATE,
        porta_manual=settings.SERIAL_PORT_MANUAL,
        intervalo_reconexao=settings.SERIAL_RECONNECT_INTERVAL_S,
    )
    nfc_reader = NfcReader(
        fila_eventos=fila_eventos,
        intervalo_reconexao=settings.NFC_RECONNECT_INTERVAL_S,
    )

    fsm = AccessControlFSM(card_registry=card_registry, enviar_comando=serial_manager.enviar)

    serial_manager.iniciar()
    nfc_reader.iniciar()

    app = App(fila_eventos=fila_eventos, fsm=fsm, empresa=settings.EMPRESA)
    app.mainloop()


if __name__ == "__main__":
    main()
