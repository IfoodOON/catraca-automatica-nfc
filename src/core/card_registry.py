"""Cadastro de cartões NFC autorizados, carregado de um arquivo JSON local."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class CardRegistry:
    """Mapeia UID de cartão -> nome do usuário autorizado.

    Pensado para ser trocado por um banco de dados no futuro sem alterar
    quem o consome: a interface pública é só `is_authorized`.
    """

    def __init__(self, cartoes_file: Path):
        self._cartoes_file = cartoes_file
        # Fica tudo em memória (dict) depois de carregado; cada escrita
        # (adicionar/remover) atualiza esse dict E regrava o arquivo.
        self._cartoes: dict[str, dict] = {}
        self.reload()

    def reload(self) -> None:
        """(Re)lê o arquivo do zero. Chamado uma vez no __init__; existe
        como método separado caso algo precise forçar uma releitura depois.
        """
        if not self._cartoes_file.exists():
            logger.warning("Arquivo de cartões não encontrado: %s", self._cartoes_file)
            self._cartoes = {}
            return

        with open(self._cartoes_file, encoding="utf-8") as f:
            self._cartoes = json.load(f)

    def is_authorized(self, uid: str) -> str | None:
        """Retorna o nome do usuário se o UID estiver autorizado, senão None.

        É a única coisa que a máquina de estados (access_control.py)
        precisa saber sobre cartões — ela nunca mexe no dict diretamente.
        """
        cartao = self._cartoes.get(uid.upper())
        return cartao["nome"] if cartao else None

    def listar(self) -> dict[str, str]:
        """Retorna {uid: nome} de todos os cartões cadastrados — usado pela
        tela de administração pra montar a lista na tela.
        """
        return {uid: dados["nome"] for uid, dados in self._cartoes.items()}

    def adicionar(self, uid: str, nome: str) -> None:
        # UID sempre em maiúsculas, pra bater com o formato salvo por
        # is_authorized e com o que o leitor NFC devolve (hex maiúsculo).
        self._cartoes[uid.upper()] = {"nome": nome}
        self._salvar()

    def remover(self, uid: str) -> None:
        self._cartoes.pop(uid.upper(), None)
        self._salvar()

    def _salvar(self) -> None:
        with open(self._cartoes_file, "w", encoding="utf-8") as f:
            json.dump(self._cartoes, f, ensure_ascii=False, indent=2)
