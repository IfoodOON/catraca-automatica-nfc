"""Ponto de entrada da aplicação da catraca automatizada (LAB 220)."""

import logging
import queue

import config.settings as settings
from core.access_control import AccessControlFSM
from core.admin_auth import AdminAuth
from core.card_registry import CardRegistry
from gui.app import App
from hardware.nfc_reader import NfcReader
from hardware.serial_comm import SerialManager

# Configura o log padrão do Python: tudo que os módulos chamarem via
# `logging.getLogger(__name__).info(...)` (ou .warning/.error) aparece no
# terminal com data/hora, nível e nome do módulo que gerou a mensagem.
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def main() -> None:
    # Fila compartilhada: Serial e NFC rodam em threads separadas e só
    # colocam eventos aqui (fila_eventos.put(...)); quem consome é a GUI,
    # na thread principal, evitando qualquer acesso a widgets fora dela.
    fila_eventos: queue.Queue = queue.Queue()

    # Cadastro de cartões autorizados e senha da tela de administração,
    # ambos carregados de arquivos JSON locais (ver src/config/).
    card_registry = CardRegistry(settings.CARTOES_FILE)
    admin_auth = AdminAuth(settings.ADMIN_FILE)

    # Comunicação com o Arduino (sensor + servo + relé) via Serial.
    serial_manager = SerialManager(
        fila_eventos=fila_eventos,
        baud_rate=settings.SERIAL_BAUD_RATE,
        porta_manual=settings.SERIAL_PORT_MANUAL,
        intervalo_reconexao=settings.SERIAL_RECONNECT_INTERVAL_S,
    )
    # Comunicação com o leitor NFC USB via pyscard — independente do Arduino.
    nfc_reader = NfcReader(
        fila_eventos=fila_eventos,
        intervalo_reconexao=settings.NFC_RECONNECT_INTERVAL_S,
    )

    # Máquina de estados do fluxo de acesso: recebe os eventos e decide
    # quando mandar "ABRIR" pro Arduino (via serial_manager.enviar).
    fsm = AccessControlFSM(card_registry=card_registry, enviar_comando=serial_manager.enviar)

    # Cada .iniciar() sobe sua própria thread de leitura em segundo plano.
    serial_manager.iniciar()
    nfc_reader.iniciar()

    # A janela principal drena a fila periodicamente (ver App._processar_fila)
    # e é quem efetivamente "roda" o programa a partir daqui.
    app = App(
        fila_eventos=fila_eventos,
        fsm=fsm,
        empresa=settings.EMPRESA,
        card_registry=card_registry,
        admin_auth=admin_auth,
    )
    app.mainloop()


if __name__ == "__main__":
    main()
