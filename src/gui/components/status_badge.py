"""Indicador de status reutilizável (bolinha colorida + título + texto)."""

import customtkinter as ctk

from gui import theme


class StatusBadge(ctk.CTkFrame):
    def __init__(self, master, titulo: str, **kwargs):
        super().__init__(master, corner_radius=12, fg_color=theme.COR_PAINEL, **kwargs)

        self._ponto = ctk.CTkLabel(
            self, text="●", font=theme.FONTE_PONTO, text_color=theme.COR_NEUTRO, width=20
        )
        self._ponto.grid(row=0, column=0, rowspan=2, padx=(14, 6), pady=10)

        ctk.CTkLabel(
            self, text=titulo, font=theme.FONTE_BADGE_TITULO, text_color=theme.COR_TEXTO_SECUNDARIO, anchor="w"
        ).grid(row=0, column=1, sticky="w", padx=(0, 14), pady=(10, 0))

        self._texto_status = ctk.CTkLabel(
            self, text="—", font=theme.FONTE_BADGE_STATUS, text_color=theme.COR_NEUTRO, anchor="w"
        )
        self._texto_status.grid(row=1, column=1, sticky="w", padx=(0, 14), pady=(0, 10))

        self.grid_columnconfigure(1, weight=1)

    def atualizar(self, texto: str, cor: str) -> None:
        self._ponto.configure(text_color=cor)
        self._texto_status.configure(text=texto, text_color=cor)
