"""Tipos de evento compartilhados entre hardware, core e GUI.

Serial e NFC rodam em threads separadas e só produzem `Evento`s numa fila;
quem consome (a GUI, na thread principal) decide o que fazer com cada um.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class EventoTipo(Enum):
    # Fluxo de acesso (Arduino / sensor / servo)
    CARRO_DETECTADO = auto()
    CARRO_SAIU = auto()
    CANCELA_ABERTA = auto()
    CANCELA_FECHADA = auto()

    # Fluxo de acesso (leitor NFC)
    CARTAO_LIDO = auto()

    # Status de conexão (não fazem parte do fluxo de acesso em si)
    ARDUINO_CONECTADO = auto()
    ARDUINO_DESCONECTADO = auto()
    NFC_CONECTADO = auto()
    NFC_DESCONECTADO = auto()


CONEXAO_EVENTOS = {
    EventoTipo.ARDUINO_CONECTADO,
    EventoTipo.ARDUINO_DESCONECTADO,
    EventoTipo.NFC_CONECTADO,
    EventoTipo.NFC_DESCONECTADO,
}


@dataclass(frozen=True)
class Evento:
    tipo: EventoTipo
    dados: str | None = None
