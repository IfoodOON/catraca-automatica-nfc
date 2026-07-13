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
    """Os "estágios" possíveis do fluxo de acesso, na ordem em que acontecem."""

    IDLE = auto()  # parado, esperando um veículo chegar
    AGUARDANDO_CARTAO = auto()  # veículo detectado, esperando o cartão NFC
    ACESSO_NEGADO = auto()  # estado só de exibição (ver _on_cartao_lido)
    ABERTA = auto()  # cancela aberta, veículo passando
    FECHANDO = auto()  # veículo saiu, Arduino está fechando a cancela


# Texto mostrado na tela pra cada estado, quando não há uma mensagem
# mais específica (como "bem-vindo, Fulano!") pra sobrepor.
MENSAGENS_PADRAO = {
    Estado.IDLE: "Aguardando veículo...",
    Estado.AGUARDANDO_CARTAO: "Aproxime o cartão do leitor NFC",
    Estado.ABERTA: "Catraca aberta",
    Estado.FECHANDO: "Fechando a catraca...",
}


@dataclass(frozen=True)
class Resultado:
    """O que a FSM devolve depois de processar um evento — tudo que a GUI
    precisa pra atualizar a tela, sem precisar conhecer os detalhes internos
    da máquina de estados.
    """

    estado: Estado
    mensagem: str
    usuario: str | None = None  # nome de quem teve o acesso liberado por último
    hora_entrada: str | None = None  # horário (HH:MM:SS) desse último acesso


class AccessControlFSM:
    """Recebe um Evento de cada vez (`processar`) e devolve um Resultado.

    Não sabe nada sobre Serial, NFC ou Tkinter — só orquestra a lógica de
    quando liberar o acesso, guiada pelo `card_registry` (quem está
    autorizado) e pelo `enviar_comando` (como avisar o Arduino pra abrir).
    """

    def __init__(self, card_registry: CardRegistry, enviar_comando: Callable[[str], None]):
        self._card_registry = card_registry
        self._enviar_comando = enviar_comando
        self.estado = Estado.IDLE
        self.usuario_atual: str | None = None
        self.hora_entrada: str | None = None

    def processar(self, evento: Evento) -> Resultado:
        """Ponto de entrada único: direciona o evento pro método que sabe
        lidar com aquele tipo específico (o "_on_..." correspondente).
        """
        handler = {
            EventoTipo.CARRO_DETECTADO: self._on_carro_detectado,
            EventoTipo.CARRO_SAIU: self._on_carro_saiu,
            EventoTipo.CARTAO_LIDO: self._on_cartao_lido,
            EventoTipo.CANCELA_ABERTA: self._on_cancela_aberta,
            EventoTipo.CANCELA_FECHADA: self._on_cancela_fechada,
        }.get(evento.tipo)

        if handler is None:
            # Evento que essa máquina de estados não trata (ex: eventos de
            # conexão) — devolve o estado atual sem mudar nada.
            return self.resultado_atual()

        return handler(evento)

    def resultado_atual(self) -> Resultado:
        """Monta um Resultado a partir do estado guardado agora mesmo —
        usado tanto internamente quanto pela GUI (ex: pra redesenhar a tela
        depois que uma mensagem temporária, como "negado", expira).
        """
        return Resultado(
            self.estado,
            MENSAGENS_PADRAO[self.estado],
            usuario=self.usuario_atual,
            hora_entrada=self.hora_entrada,
        )

    def _on_carro_detectado(self, evento: Evento) -> Resultado:
        # Só reage se estava parado — evita reprocessar se o sensor
        # piscar CARRO de novo enquanto já está no meio do fluxo.
        if self.estado is Estado.IDLE:
            self.estado = Estado.AGUARDANDO_CARTAO
        return self.resultado_atual()

    def _on_carro_saiu(self, evento: Evento) -> Resultado:
        if self.estado is Estado.AGUARDANDO_CARTAO:
            # Veículo desistiu antes de apresentar o cartão: volta a esperar.
            self.estado = Estado.IDLE
        elif self.estado is Estado.ABERTA:
            # Veículo passou de verdade: o Arduino vai fechar a cancela
            # sozinho depois de alguns segundos (ver catraca_producao.ino).
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
            # O estado "de verdade" já volta a AGUARDANDO_CARTAO agora mesmo
            # (aceita o próximo cartão imediatamente); só o Resultado
            # devolvido finge por um instante que o estado é ACESSO_NEGADO,
            # pra GUI conseguir mostrar o aviso vermelho antes de voltar ao
            # texto padrão (ver App._mostrar_estado).
            self.estado = Estado.AGUARDANDO_CARTAO
            return Resultado(Estado.ACESSO_NEGADO, "Cartão não autorizado. Tente novamente.")

        logger.info("Cartão autorizado: %s (%s)", uid, nome)
        self.usuario_atual = nome
        self.hora_entrada = datetime.now().strftime("%H:%M:%S")
        self.estado = Estado.ABERTA
        self._enviar_comando("ABRIR")  # só aqui o Arduino fica sabendo que pode abrir
        return Resultado(
            self.estado,
            f"Acesso liberado — bem-vindo, {nome}!",
            usuario=self.usuario_atual,
            hora_entrada=self.hora_entrada,
        )

    def _on_cancela_aberta(self, evento: Evento) -> Resultado:
        # Confirmação do Arduino de que o servo terminou de abrir.
        self.estado = Estado.ABERTA
        return self.resultado_atual()

    def _on_cancela_fechada(self, evento: Evento) -> Resultado:
        # Confirmação do Arduino de que o servo terminou de fechar — o
        # ciclo completo acabou, volta tudo ao estado inicial.
        self.estado = Estado.IDLE
        self.usuario_atual = None
        self.hora_entrada = None
        return self.resultado_atual()
