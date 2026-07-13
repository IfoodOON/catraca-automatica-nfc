"""Tela de administração: senha de acesso + cadastro de funcionários/cartões."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from core.admin_auth import AdminAuth
from core.card_registry import CardRegistry
from gui import theme


class SenhaDialog(ctk.CTkToplevel):
    """Janela modal pedindo a senha antes de abrir a AdminWindow.
    `CTkToplevel` = uma janela separada, mas "filha" da principal."""

    def __init__(self, master, admin_auth: AdminAuth, ao_autenticar: Callable[[], None]):
        super().__init__(master)
        self._admin_auth = admin_auth
        self._ao_autenticar = ao_autenticar

        self.title("Área restrita")
        self.geometry("360x200")
        self.resizable(False, False)
        self.configure(fg_color=theme.COR_FUNDO)
        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(
            self, text="Digite a senha de administração", font=theme.FONTE_USUARIO, text_color=theme.COR_TEXTO
        ).pack(pady=(24, 8))

        self._entrada_senha = ctk.CTkEntry(self, show="*", width=220)
        self._entrada_senha.pack(pady=4)
        self._entrada_senha.bind("<Return>", lambda _evento: self._confirmar())
        self._entrada_senha.focus()

        self._label_erro = ctk.CTkLabel(self, text="", font=theme.FONTE_DATA, text_color=theme.COR_ERRO)
        self._label_erro.pack(pady=4)

        botoes = ctk.CTkFrame(self, fg_color="transparent")
        botoes.pack(pady=12)
        ctk.CTkButton(botoes, text="Cancelar", fg_color=theme.COR_NEUTRO, command=self.destroy).pack(
            side="left", padx=6
        )
        ctk.CTkButton(botoes, text="Confirmar", command=self._confirmar).pack(side="left", padx=6)

    def _confirmar(self) -> None:
        senha = self._entrada_senha.get()
        if self._admin_auth.verificar_senha(senha):
            self.destroy()
            self._ao_autenticar()
        else:
            self._label_erro.configure(text="Senha incorreta")
            self._entrada_senha.delete(0, "end")


class AdminWindow(ctk.CTkToplevel):
    """Tela de cadastro: lista os cartões existentes e permite capturar um
    UID novo aproximando o cartão do leitor (via `ativar_captura`, recebido
    de fora — ver `App.ativar_modo_captura`), sem passar pelo fluxo normal
    de acesso.
    """

    def __init__(
        self,
        master,
        card_registry: CardRegistry,
        ativar_captura: Callable[[Callable[[str], None]], None],
        desativar_captura: Callable[[], None],
    ):
        super().__init__(master)
        self._card_registry = card_registry
        self._ativar_captura = ativar_captura
        self._desativar_captura = desativar_captura
        self._uid_capturado: str | None = None

        self.title("Cadastro de Funcionários — LAB 220")
        self.geometry("560x640")
        self.configure(fg_color=theme.COR_FUNDO)
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)

        ctk.CTkLabel(
            self, text="Funcionários cadastrados", font=theme.FONTE_EMPRESA, text_color=theme.COR_TEXTO
        ).pack(pady=(20, 10), padx=20, anchor="w")

        self._lista = ctk.CTkScrollableFrame(self, fg_color=theme.COR_PAINEL)
        self._lista.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        secao_novo = ctk.CTkFrame(self, corner_radius=12, fg_color=theme.COR_PAINEL)
        secao_novo.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            secao_novo, text="Novo cadastro", font=theme.FONTE_USUARIO, text_color=theme.COR_TEXTO
        ).pack(anchor="w", padx=16, pady=(14, 4))

        self._botao_aguardar = ctk.CTkButton(secao_novo, text="Aguardar cartão", command=self._iniciar_captura)
        self._botao_aguardar.pack(anchor="w", padx=16, pady=4)

        self._label_captura = ctk.CTkLabel(secao_novo, text="", font=theme.FONTE_DATA, text_color=theme.COR_ALERTA)
        self._label_captura.pack(anchor="w", padx=16)

        self._entrada_nome = ctk.CTkEntry(secao_novo, placeholder_text="Nome do funcionário", width=300)
        self._entrada_nome.pack(anchor="w", padx=16, pady=(8, 4))

        self._botao_salvar = ctk.CTkButton(secao_novo, text="Salvar", command=self._salvar, state="disabled")
        self._botao_salvar.pack(anchor="w", padx=16, pady=(4, 16))

        self._popular_lista()

    def _popular_lista(self) -> None:
        for widget in self._lista.winfo_children():
            widget.destroy()

        cartoes = self._card_registry.listar()
        if not cartoes:
            ctk.CTkLabel(
                self._lista, text="Nenhum cartão cadastrado ainda.", text_color=theme.COR_TEXTO_SECUNDARIO
            ).pack(pady=12)
            return

        for uid, nome in cartoes.items():
            linha = ctk.CTkFrame(self._lista, fg_color="transparent")
            linha.pack(fill="x", pady=4)
            ctk.CTkLabel(
                linha, text=nome, font=theme.FONTE_USUARIO, text_color=theme.COR_TEXTO, anchor="w", width=180
            ).pack(side="left", padx=(4, 8))
            ctk.CTkLabel(
                linha, text=uid, font=theme.FONTE_DATA, text_color=theme.COR_TEXTO_SECUNDARIO, anchor="w"
            ).pack(side="left", expand=True, fill="x")
            ctk.CTkButton(
                linha,
                text="Remover",
                width=80,
                fg_color=theme.COR_ERRO,
                hover_color="#c0392b",
                command=lambda u=uid: self._remover(u),
            ).pack(side="right", padx=4)

    def _remover(self, uid: str) -> None:
        self._card_registry.remover(uid)
        self._popular_lista()

    def _iniciar_captura(self) -> None:
        # Registra `_on_cartao_capturado` como o callback que a App vai
        # chamar assim que o próximo cartão for lido (em vez de tratá-lo
        # como uma tentativa normal de acesso).
        self._uid_capturado = None
        self._botao_salvar.configure(state="disabled")
        self._label_captura.configure(text="Aproxime o cartão do leitor...")
        self._ativar_captura(self._on_cartao_capturado)

    def _on_cartao_capturado(self, uid: str) -> None:
        self._uid_capturado = uid
        self._label_captura.configure(text=f"Cartão lido: {uid}")
        self._botao_salvar.configure(state="normal")
        self._desativar_captura()  # já capturou; volta o app ao modo normal

    def _salvar(self) -> None:
        nome = self._entrada_nome.get().strip()
        if not self._uid_capturado or not nome:
            return
        self._card_registry.adicionar(self._uid_capturado, nome)
        self._uid_capturado = None
        self._entrada_nome.delete(0, "end")
        self._label_captura.configure(text="Cadastrado!")
        self._botao_salvar.configure(state="disabled")
        self._popular_lista()

    def _ao_fechar(self) -> None:
        self._desativar_captura()
        self.destroy()
