"""Relógio com data/hora/ano, atualizado a cada segundo."""

from datetime import datetime

import customtkinter as ctk

from gui import theme


class RelogioFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._label_hora = ctk.CTkLabel(self, text="", font=theme.FONTE_RELOGIO, text_color=theme.COR_TEXTO)
        self._label_hora.pack(anchor="e")

        self._label_data = ctk.CTkLabel(self, text="", font=theme.FONTE_DATA, text_color=theme.COR_TEXTO_SECUNDARIO)
        self._label_data.pack(anchor="e")

        self._atualizar()

    def _atualizar(self) -> None:
        agora = datetime.now()
        self._label_hora.configure(text=agora.strftime("%H:%M:%S"))
        self._label_data.configure(text=agora.strftime("%d/%m/%Y") + f"  •  Ano {agora.year}")
        self.after(1000, self._atualizar)
