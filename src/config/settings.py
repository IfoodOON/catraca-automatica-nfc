"""Configuração central da aplicação."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

EMPRESA = "LAB 220"

# --- Serial (Arduino) ---
SERIAL_BAUD_RATE = 9600
SERIAL_PORT_MANUAL = None  # ex: "COM5" — usado se a auto-detecção falhar
SERIAL_RECONNECT_INTERVAL_S = 3

# --- Cadastro de cartões NFC ---
CARTOES_FILE = BASE_DIR / "cartoes.json"

# --- NFC ---
NFC_RECONNECT_INTERVAL_S = 3
