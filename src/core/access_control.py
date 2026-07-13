"""Máquina de estados do fluxo de acesso — espelha docs/fluxograma.md.

A decisão de autorizar ou negar um cartão acontece inteiramente aqui, no PC;
o Arduino não sabe nada sobre NFC, só executa o comando "ABRIR" que este
módulo manda quando um cartão é autorizado.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from core.card_registry import CardRegistry
from core.eventos import Evento, EventoTipo
from enum import Enum, auto

logger = logging.getLogger(__name__)


class Estado(Enum):
    IDLE = auto()
    AGUARDANDO_CARTAO = auto()
    ACESSO_NEGADO = auto()
    ABERTA = auto()
    FECHANDO = auto()


MENSAGENS_PADRAO = {
    Estado.IDLE: "Aguardando veículo...",
    Estado.AGUARDANDO_CARTAO: "Aproxime o cartão do leitor NFC",
    Estado.ABERTA: "Catraca aberta",
    Estado.FECHANDO: "Fechando a catraca...",
}


@dataclass(frozen=True)
class Resultado:
    estado: Estado
    mensagem: str
    usuario: str | None = None
    hora_entrada: str | None = None


class AccessControlFSM:
    def __init__(self, card_registry: CardRegistry, enviar_comando: Callable[[str], None]):
        self._card_registry = card_registry
        self._enviar_comando = enviar_comando
        self.estado = Estado.IDLE
        self.usuario_atual: str | None = None
        self.hora_entrada: str | None = None

    def processar(self, evento: Evento) -> Resultado:
        handler = {
            EventoTipo.CARRO_DETECTADO: self._on_carro_detectado,
            EventoTipo.CARRO_SAIU: self._on_carro_saiu,
            EventoTipo.CARTAO_LIDO: self._on_cartao_lido,
            EventoTipo.CANCELA_ABERTA: self._on_cancela_aberta,
            EventoTipo.CANCELA_FECHADA: self._on_cancela_fechada,
        }.get(evento.tipo)

        if handler is None:
            return self.resultado_atual()

        return handler(evento)

    def resultado_atual(self) -> Resultado:
        return Resultado(
            self.estado,
            MENSAGENS_PADRAO[self.estado],
            usuario=self.usuario_atual,
            hora_entrada=self.hora_entrada,
        )

    def _on_carro_detectado(self, evento: Evento) -> Resultado:
        if self.estado is Estado.IDLE:
            self.estado = Estado.AGUARDANDO_CARTAO
        return self.resultado_atual()

    def _on_carro_saiu(self, evento: Evento) -> Resultado:
        if self.estado is Estado.AGUARDANDO_CARTAO:
            self.estado = Estado.IDLE
        elif self.estado is Estado.ABERTA:
            self.estado = Estado.FECHANDO
        return self.resultado_atual()

    def _on_cartao_lido(self, evento: Evento) -> Resultado:
        if self.estado is not Estado.AGUARDANDO_CARTAO:
            # Cartão lido fora de hora (ex: sem veículo presente) — ignora.
            return self.resultado_atual()

        uid = evento.dados or ""
        nome = self._card_registry.is_authorized(uid)

        if nome is None:
            logger.info("Cartão negado: %s", uid)
            # Continua aguardando um novo cartão, como no fluxograma.
            self.estado = Estado.AGUARDANDO_CARTAO
            return Resultado(Estado.ACESSO_NEGADO, "Cartão não autorizado. Tente novamente.")

        logger.info("Cartão autorizado: %s (%s)", uid, nome)
        self.usuario_atual = nome
        self.hora_entrada = datetime.now().strftime("%H:%M:%S")
        self.estado = Estado.ABERTA
        self._enviar_comando("ABRIR")
        return Resultado(
            self.estado,
            f"Acesso liberado — bem-vindo, {nome}!",
            usuario=self.usuario_atual,
            hora_entrada=self.hora_entrada,
        )

    def _on_cancela_aberta(self, evento: Evento) -> Resultado:
        self.estado = Estado.ABERTA
        return self.resultado_atual()

    def _on_cancela_fechada(self, evento: Evento) -> Resultado:
        self.estado = Estado.IDLE
        self.usuario_atual = None
        self.hora_entrada = None
        return self.resultado_atual()
