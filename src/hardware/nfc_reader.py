"""Comunicação com o leitor NFC USB via pyscard (PC/SC).

Independente do Arduino: o leitor fala diretamente com o PC, não passa
pela Serial.
"""

from __future__ import annotations

import logging
import queue
import threading
import time

from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.Exceptions import CardConnectionException, NoCardException
from smartcard.ReaderMonitoring import ReaderMonitor, ReaderObserver
from smartcard.System import readers as pcsc_readers

from core.eventos import Evento, EventoTipo

logger = logging.getLogger(__name__)

APDU_GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]  # comando PC/SC padrão para ler o UID


class NfcReader:
    """Publica CARTAO_LIDO (com o UID em hex) e NFC_CONECTADO/NFC_DESCONECTADO na fila."""

    def __init__(self, fila_eventos: queue.Queue, intervalo_reconexao: float):
        self._fila = fila_eventos
        self._intervalo_reconexao = intervalo_reconexao
        self._card_monitor: CardMonitor | None = None
        self._card_observer: CardObserver | None = None
        self._reader_monitor: ReaderMonitor | None = None
        self._reader_observer: ReaderObserver | None = None

    def iniciar(self) -> None:
        threading.Thread(target=self._configurar_com_retry, daemon=True).start()

    def parar(self) -> None:
        if self._card_monitor and self._card_observer:
            self._card_monitor.deleteObserver(self._card_observer)
        if self._reader_monitor and self._reader_observer:
            self._reader_monitor.deleteObserver(self._reader_observer)

    def _configurar_com_retry(self) -> None:
        # Roda numa thread própria. Se o serviço PC/SC do Windows não
        # estiver disponível ainda (ex: app abriu antes do serviço subir),
        # tenta de novo periodicamente em vez de travar o app inteiro.
        while True:
            try:
                self._configurar_monitores()
                return
            except Exception:
                logger.exception("Falha ao iniciar monitoramento NFC, tentando novamente...")
                self._fila.put(Evento(EventoTipo.NFC_DESCONECTADO))
                time.sleep(self._intervalo_reconexao)

    def _configurar_monitores(self) -> None:
        # CardMonitor/ReaderMonitor são do pyscard: cada um já sobe sua
        # própria thread interna e chama `update(...)` do observer sempre
        # que um cartão é aproximado ou um leitor conecta/desconecta —
        # não precisamos fazer polling manual aqui.
        self._card_observer = _CartaoLidoObserver(self._fila)
        self._card_monitor = CardMonitor()
        self._card_monitor.addObserver(self._card_observer)

        self._reader_observer = _LeitorStatusObserver(self._fila)
        self._reader_monitor = ReaderMonitor()
        self._reader_monitor.addObserver(self._reader_observer)

        # Avisa logo de cara se já tem (ou não) leitor plugado, sem esperar
        # o próximo evento de conexão/desconexão do ReaderObserver.
        evento_inicial = EventoTipo.NFC_CONECTADO if pcsc_readers() else EventoTipo.NFC_DESCONECTADO
        self._fila.put(Evento(evento_inicial))


class _CartaoLidoObserver(CardObserver):
    """Chamado pelo pyscard sempre que a lista de cartões presentes no
    leitor muda (`update`) — é aqui que a gente efetivamente lê o UID.
    """

    def __init__(self, fila_eventos: queue.Queue):
        self._fila = fila_eventos

    def update(self, observable, actions):
        cartoes_adicionados, _cartoes_removidos = actions
        for cartao in cartoes_adicionados:
            uid = self._ler_uid(cartao)
            if uid:
                self._fila.put(Evento(EventoTipo.CARTAO_LIDO, uid))

    @staticmethod
    def _ler_uid(cartao) -> str | None:
        try:
            # Protocolo PC/SC padrão: conecta no cartão e manda o comando
            # "Get Data" (APDU_GET_UID) pra pedir o UID dele.
            conexao = cartao.createConnection()
            conexao.connect()
            resposta, sw1, sw2 = conexao.transmit(APDU_GET_UID)
            if (sw1, sw2) != (0x90, 0x00):  # 90 00 = "sucesso" no padrão PC/SC
                logger.warning("Falha ao ler UID do cartão (sw=%02X%02X)", sw1, sw2)
                return None
            # UID vem como lista de bytes; convertemos pra string hex
            # (ex: [5, 130, 136] -> "058288"), igual ao formato salvo em cartoes.json.
            return "".join(f"{byte:02X}" for byte in resposta)
        except (NoCardException, CardConnectionException):
            logger.exception("Erro ao ler cartão NFC")
            return None


class _LeitorStatusObserver(ReaderObserver):
    """Chamado pelo pyscard quando um leitor NFC é conectado/desconectado
    do PC (não confundir com cartão sendo aproximado/afastado)."""

    def __init__(self, fila_eventos: queue.Queue):
        self._fila = fila_eventos

    def update(self, observable, actions):
        leitores_adicionados, leitores_removidos = actions
        if leitores_adicionados:
            self._fila.put(Evento(EventoTipo.NFC_CONECTADO))
        if leitores_removidos and not pcsc_readers():
            # Só avisa "desconectado" se não sobrou nenhum outro leitor
            # (o usuário pode ter mais de um plugado ao mesmo tempo).
            self._fila.put(Evento(EventoTipo.NFC_DESCONECTADO))
