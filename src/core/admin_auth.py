"""Autenticação simples para a tela de cadastro de funcionários/cartões.

Não é segurança de nível bancário — é só um freio contra qualquer pessoa
que passe na catraca abrir o cadastro sozinha. A senha fica com hash
SHA-256 num arquivo local gitignorado, nunca em texto puro no repositório.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SENHA_PADRAO = "lab220"


def _hash(senha: str) -> str:
    # Nunca comparamos/guardamos a senha em texto puro, só esse hash.
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


class AdminAuth:
    def __init__(self, admin_file: Path):
        self._admin_file = admin_file
        # Primeira vez que o app roda nesta máquina: cria o arquivo
        # automaticamente com a senha padrão, pra não travar o usuário.
        if not self._admin_file.exists():
            logger.warning(
                "Arquivo de admin não encontrado, criando com senha padrão '%s'. "
                "Troque assim que possível.",
                SENHA_PADRAO,
            )
            self.definir_senha(SENHA_PADRAO)

    def verificar_senha(self, senha: str) -> bool:
        with open(self._admin_file, encoding="utf-8") as f:
            dados = json.load(f)
        return _hash(senha) == dados.get("senha_hash")

    def definir_senha(self, nova_senha: str) -> None:
        with open(self._admin_file, "w", encoding="utf-8") as f:
            json.dump({"senha_hash": _hash(nova_senha)}, f, indent=2)
