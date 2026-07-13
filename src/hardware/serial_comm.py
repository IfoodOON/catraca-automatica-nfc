"""Comunicação Serial com o Arduino."""

from __future__ import annotations

import logging
import queue
import threading
import time

import serial
from serial.tools import list_ports

from core.eventos import Evento, EventoTipo

logger = logging.getLogger(__name__)

ARDUINO_VIDS = {
    0x2341,  # Arduino LLC (placas oficiais)
    0x1A86,  # WCH CH340 (muito comum em clones de Uno/Nano)
    0x10C4,  # Silicon Labs CP210x (outro chip comum em clones)
    0x0403,  # FTDI (alguns clones/shields)
}

COMANDO_PARA_EVENTO = {
    "CARRO": EventoTipo.CARRO_DETECTADO,
    "SEM_CARRO": EventoTipo.CARRO_SAIU,
    "ABERTA": EventoTipo.CANCELA_ABERTA,
    "FECHADA": EventoTipo.CANCELA_FECHADA,
}


class SerialManager:
    """Lê comandos do Arduino numa thread própria e publica eventos na fila.

    Nunca derruba a aplicação por causa de porta ausente/instável: tenta
    reconectar periodicamente e avisa a fila quando o status muda.
    """

    def __init__(
        self,
        fila_eventos: queue.Queue,
        baud_rate: int,
        porta_manual: str | None,
        intervalo_reconexao: float,
    ):
        self._fila = fila_eventos
        self._baud_rate = baud_rate
        self._porta_manual = porta_manual
        self._intervalo_reconexao = intervalo_reconexao
        self._serial: serial.Serial | None = None
        self._write_lock = threading.Lock()
        self._parar = threading.Event()
        self._conectado = False

    @property
    def conectado(self) -> bool:
        return self._conectado

    def iniciar(self) -> None:
        threading.Thread(target=self._loop, daemon=True).start()

    def parar(self) -> None:
        self._parar.set()

    def enviar(self, comando: str) -> None:
        if not self._conectado or self._serial is None:
            logger.warning("Tentativa de enviar '%s' sem conexão com o Arduino", comando)
            return
        with self._write_lock:
            try:
                self._serial.write(f"{comando}\n".encode("utf-8"))
            except (serial.SerialException, OSError):
                logger.exception("Falha ao enviar comando '%s'", comando)
                self._marcar_desconectado()

    def _loop(self) -> None:
        while not self._parar.is_set():
            if not self._conectado:
                self._tentar_conectar()
                if not self._conectado:
                    time.sleep(self._intervalo_reconexao)
                continue

            try:
                linha = self._serial.readline().decode("utf-8", errors="ignore").strip()
            except (serial.SerialException, OSError):
                logger.exception("Conexão com o Arduino perdida")
                self._marcar_desconectado()
                continue

            if not linha:
                continue

            evento_tipo = COMANDO_PARA_EVENTO.get(linha)
            if evento_tipo is not None:
                self._fila.put(Evento(evento_tipo))
            else:
                logger.debug("Linha Serial não reconhecida: %s", linha)

    def _tentar_conectar(self) -> None:
        porta = self._porta_manual or self._detectar_porta()
        if porta is None:
            return

        try:
            self._serial = serial.Serial(porta, self._baud_rate, timeout=1)
            time.sleep(2)  # Arduino reseta ao abrir a porta serial
            self._conectado = True
            self._fila.put(Evento(EventoTipo.ARDUINO_CONECTADO, porta))
            logger.info("Conectado ao Arduino em %s", porta)
        except (serial.SerialException, OSError):
            self._serial = None

    def _marcar_desconectado(self) -> None:
        if self._conectado:
            self._conectado = False
            self._fila.put(Evento(EventoTipo.ARDUINO_DESCONECTADO))
        if self._serial is not None:
            try:
                self._serial.close()
            except (serial.SerialException, OSError):
                pass
            self._serial = None

    @staticmethod
    def _detectar_porta() -> str | None:
        for porta in list_ports.comports():
            descricao = (porta.description or "").lower()
            if "arduino" in descricao or "ch340" in descricao or porta.vid in ARDUINO_VIDS:
                return porta.device
        return None
