"""Configuração central da aplicação."""

import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    # Rodando como .exe (PyInstaller): __file__ apontaria pra uma pasta
    # temporária que é recriada a cada execução (modo --onefile), então os
    # dados (cartões/senha) ficam salvos ao lado do próprio .exe pra persistir
    # entre execuções.
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

EMPRESA = "LAB 220"

# --- Serial (Arduino) ---
SERIAL_BAUD_RATE = 9600
SERIAL_PORT_MANUAL = None  # ex: "COM5" — usado se a auto-detecção falhar
SERIAL_RECONNECT_INTERVAL_S = 3

# --- Cadastro de cartões NFC ---
CARTOES_FILE = BASE_DIR / "cartoes.json"

# --- Administração (tela de cadastro) ---
ADMIN_FILE = BASE_DIR / "admin.json"

# --- NFC ---
NFC_RECONNECT_INTERVAL_S = 3
