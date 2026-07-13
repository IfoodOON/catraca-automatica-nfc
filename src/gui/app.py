"""Janela principal da aplicação."""

from __future__ import annotations

import queue
from typing import Callable

import customtkinter as ctk

from core.access_control import AccessControlFSM, Estado, Resultado
from core.admin_auth import AdminAuth
from core.card_registry import CardRegistry
from core.eventos import CONEXAO_EVENTOS, Evento, EventoTipo
from gui import theme
from gui.admin import AdminWindow, SenhaDialog
from gui.components.clock import RelogioFrame
from gui.components.status_badge import StatusBadge

INTERVALO_POLLING_MS = 100
DURACAO_MENSAGEM_NEGADO_MS = 2500

CLIQUES_PARA_ADMIN = 6
JANELA_CLIQUES_MS = 2000

CORES_POR_ESTADO = {
    Estado.IDLE: theme.COR_NEUTRO,
    Estado.AGUARDANDO_CARTAO: theme.COR_ALERTA,
    Estado.ACESSO_NEGADO: theme.COR_ERRO,
    Estado.ABERTA: theme.COR_OK,
    Estado.FECHANDO: theme.COR_ALERTA,
}


class App(ctk.CTk):
    def __init__(
        self,
        fila_eventos: queue.Queue,
        fsm: AccessControlFSM,
        empresa: str,
        card_registry: CardRegistry,
        admin_auth: AdminAuth,
    ):
        super().__init__()

        ctk.set_appearance_mode("dark")

        self._fila = fila_eventos
        self._fsm = fsm
        self._empresa = empresa
        self._card_registry = card_registry
        self._admin_auth = admin_auth

        self._callback_captura: Callable[[str], None] | None = None
        self._contador_cliques_secretos = 0
        self._id_reset_cliques_secretos: str | None = None

        self.title(f"Catraca Automatizada — {empresa}")
        self.minsize(800, 540)
        self.configure(fg_color=theme.COR_FUNDO)

        self._centralizar_janela(960, 600)
        self._construir_layout()
        self._mostrar_estado(self._fsm.resultado_atual())
        self.after(INTERVALO_POLLING_MS, self._processar_fila)

    def _centralizar_janela(self, largura: int, altura: int) -> None:
        tela_largura = self.winfo_screenwidth()
        tela_altura = self.winfo_screenheight()
        x = (tela_largura - largura) // 2
        y = (tela_altura - altura) // 2 - 20  # levemente acima do centro, reservando espaço pra barra de tarefas
        self.geometry(f"{largura}x{altura}+{x}+{max(y, 0)}")

    def _registrar_clique_secreto(self, _evento) -> None:
        self._contador_cliques_secretos += 1

        if self._id_reset_cliques_secretos is not None:
            self.after_cancel(self._id_reset_cliques_secretos)
        self._id_reset_cliques_secretos = self.after(JANELA_CLIQUES_MS, self._resetar_cliques_secretos)

        if self._contador_cliques_secretos >= CLIQUES_PARA_ADMIN:
            self._resetar_cliques_secretos()
            self._abrir_dialogo_senha()

    def _resetar_cliques_secretos(self) -> None:
        self._contador_cliques_secretos = 0
        if self._id_reset_cliques_secretos is not None:
            self.after_cancel(self._id_reset_cliques_secretos)
            self._id_reset_cliques_secretos = None

    def _abrir_dialogo_senha(self) -> None:
        SenhaDialog(self, self._admin_auth, self._abrir_admin)

    def _abrir_admin(self) -> None:
        AdminWindow(self, self._card_registry, self.ativar_modo_captura, self.desativar_modo_captura)

    def ativar_modo_captura(self, callback: Callable[[str], None]) -> None:
        self._callback_captura = callback

    def desativar_modo_captura(self) -> None:
        self._callback_captura = None

    def _construir_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Cabeçalho
        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        cabecalho.grid_columnconfigure(0, weight=1)

        label_empresa = ctk.CTkLabel(
            cabecalho, text=self._empresa, font=theme.FONTE_EMPRESA, text_color=theme.COR_TEXTO
        )
        label_empresa.grid(row=0, column=0, sticky="w")
        # Sem botão nem área visível: 6 cliques no nome da empresa (canto
        # superior esquerdo) abrem a tela de administração.
        label_empresa.bind("<Button-1>", self._registrar_clique_secreto)
        ctk.CTkLabel(
            cabecalho,
            text="Controle de acesso automatizado",
            font=theme.FONTE_DATA,
            text_color=theme.COR_TEXTO_SECUNDARIO,
        ).grid(row=1, column=0, sticky="w")

        RelogioFrame(cabecalho).grid(row=0, column=1, rowspan=2, sticky="e")

        # Painel central de mensagem
        painel = ctk.CTkFrame(self, corner_radius=16, fg_color=theme.COR_PAINEL)
        painel.grid(row=1, column=0, sticky="nsew", padx=24, pady=10)
        painel.grid_columnconfigure(0, weight=1)
        painel.grid_rowconfigure(0, weight=1)

        conteudo = ctk.CTkFrame(painel, fg_color="transparent")
        conteudo.grid(row=0, column=0)

        self._label_mensagem = ctk.CTkLabel(
            conteudo, text="", font=theme.FONTE_MENSAGEM, text_color=theme.COR_TEXTO, wraplength=640, justify="center"
        )
        self._label_mensagem.pack(pady=(0, 8))

        self._label_usuario = ctk.CTkLabel(
            conteudo, text="", font=theme.FONTE_USUARIO, text_color=theme.COR_TEXTO_SECUNDARIO
        )
        self._label_usuario.pack()

        # Linha de indicadores de status
        badges = ctk.CTkFrame(self, fg_color="transparent")
        badges.grid(row=2, column=0, sticky="ew", padx=24, pady=(10, 20))
        for i in range(4):
            badges.grid_columnconfigure(i, weight=1, uniform="badge")

        self._badge_arduino = StatusBadge(badges, "Arduino")
        self._badge_arduino.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self._badge_nfc = StatusBadge(badges, "Leitor NFC")
        self._badge_nfc.grid(row=0, column=1, sticky="ew", padx=8)

        self._badge_sensor = StatusBadge(badges, "Sensor de proximidade")
        self._badge_sensor.grid(row=0, column=2, sticky="ew", padx=8)

        self._badge_catraca = StatusBadge(badges, "Catraca")
        self._badge_catraca.grid(row=0, column=3, sticky="ew", padx=(8, 0))

        self._badge_arduino.atualizar("Desconectado", theme.COR_ERRO)
        self._badge_nfc.atualizar("Desconectado", theme.COR_ERRO)

    def _processar_fila(self) -> None:
        try:
            while True:
                evento = self._fila.get_nowait()
                self._tratar_evento(evento)
        except queue.Empty:
            pass
        self.after(INTERVALO_POLLING_MS, self._processar_fila)

    def _tratar_evento(self, evento: Evento) -> None:
        if evento.tipo in CONEXAO_EVENTOS:
            self._atualizar_badge_conexao(evento)
            return

        if evento.tipo is EventoTipo.CARTAO_LIDO and self._callback_captura is not None:
            self._callback_captura(evento.dados)
            return

        resultado = self._fsm.processar(evento)
        self._mostrar_estado(resultado)

    def _atualizar_badge_conexao(self, evento: Evento) -> None:
        if evento.tipo is EventoTipo.ARDUINO_CONECTADO:
            self._badge_arduino.atualizar("Conectado", theme.COR_OK)
        elif evento.tipo is EventoTipo.ARDUINO_DESCONECTADO:
            self._badge_arduino.atualizar("Desconectado", theme.COR_ERRO)
        elif evento.tipo is EventoTipo.NFC_CONECTADO:
            self._badge_nfc.atualizar("Conectado", theme.COR_OK)
        elif evento.tipo is EventoTipo.NFC_DESCONECTADO:
            self._badge_nfc.atualizar("Desconectado", theme.COR_ERRO)

    def _mostrar_estado(self, resultado: Resultado) -> None:
        cor = CORES_POR_ESTADO[resultado.estado]
        self._label_mensagem.configure(text=resultado.mensagem, text_color=cor)

        if resultado.usuario:
            self._label_usuario.configure(
                text=f"Usuário: {resultado.usuario}    •    Entrada: {resultado.hora_entrada}"
            )
        else:
            self._label_usuario.configure(text="")

        veiculo_presente = resultado.estado is not Estado.IDLE
        if veiculo_presente:
            self._badge_sensor.atualizar("Veículo detectado", theme.COR_ALERTA)
        else:
            self._badge_sensor.atualizar("Aguardando veículo", theme.COR_NEUTRO)

        if resultado.estado is Estado.ABERTA:
            self._badge_catraca.atualizar("Aberta", theme.COR_OK)
        else:
            self._badge_catraca.atualizar("Fechada", theme.COR_NEUTRO)

        # ACESSO_NEGADO é só um estado de exibição transitório — a FSM já
        # voltou para AGUARDANDO_CARTAO por trás. Depois de um tempo, volta a
        # mostrar a mensagem padrão do estado real.
        if resultado.estado is Estado.ACESSO_NEGADO:
            self.after(DURACAO_MENSAGEM_NEGADO_MS, self._revalidar_mensagem_padrao)

    def _revalidar_mensagem_padrao(self) -> None:
        self._mostrar_estado(self._fsm.resultado_atual())
