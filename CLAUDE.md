# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Vehicle access-control gate ("catraca") for **LAB 220**. An Arduino drives the physical hardware (proximity sensor, servo-controlled gate, relay/LED); a Python desktop app (CustomTkinter) reads NFC cards, talks to the Arduino over Serial, and shows live status in a GUI. Target deliverable is a standalone Windows `.exe`.

## Commands

```bash
pip install -r requirements.txt        # install dependencies
python src/main.py                     # run the app
pyinstaller --noconfirm --onefile --windowed --name CatracaLAB220 --add-data "src/resources;resources" src/main.py
                                        # build the Windows executable -> dist/CatracaLAB220.exe
```

There is no test suite yet. Arduino sketches are compiled/uploaded from the Arduino IDE, not from this Python toolchain.

## Architecture

**Two independent hardware links, not one:**
- Arduino <-> PC: USB Serial, 9600 baud. Arduino owns the proximity sensor, the gate servo, and the relay/LED — Python never drives GPIO directly, only sends/receives these Serial lines.
- NFC reader <-> PC: a USB reader (ACR122U-class) talks to Python directly via `pyscard`. It is **not** wired through the Arduino.

**Serial protocol (defined by the Arduino sketch, treat as a fixed contract):**
- Arduino -> PC: `CARRO` (vehicle detected), `SEM_CARRO` (vehicle left), `ABERTA` (gate finished opening), `FECHADA` (gate finished closing)
- PC -> Arduino: `ABRIR` (open the gate) — only has an effect if the gate isn't already open

**Access flow** (see `docs/` for the authoritative flowchart once provided): idle -> wait for vehicle (`CARRO` received) -> GUI prompts for NFC card -> card read via pyscard -> if authorized, send `ABRIR` and show granted -> if not, show denied, gate stays shut -> after the vehicle clears (`SEM_CARRO` + Arduino's internal 3s delay) the Arduino closes the gate itself and reports `FECHADA` -> back to idle.

**Folder layout:**
- `arduino/catraca_producao/` — the production sketch. **Do not modify its logic without first explaining why to the user** — it's already working hardware, and any protocol change here breaks the Python side's assumptions.
- `arduino/catraca_teste/` — a standalone test sketch (auto-opens gate on car detection, no NFC gating) used only to validate sensor/servo/relay wiring. Not part of the production flow.
- `src/hardware/` — Serial communication (Arduino) and NFC communication (reader), isolated from each other and from the GUI. Must degrade gracefully (friendly GUI message, no crash) on Arduino disconnects, COM port changes, or the NFC reader going unresponsive.
- `src/core/` — the access-flow state machine. GUI and hardware modules should talk to this through events/state, not call each other directly.
- `src/gui/` — CustomTkinter interface. Must surface: user name, company name (LAB 220), date, entry time, year, gate status, Arduino connection status, NFC reader status, proximity sensor status, and guidance messages, with visual indicators for each state in the access flow (Arduino connected/disconnected, waiting for vehicle, vehicle detected, waiting for card, authorized/refused, gate open/closed).
- `src/config/` — runtime configuration (COM port, etc.). `src/config/local_settings.py` is gitignored for anything environment-specific/sensitive (e.g. an authorized-card list) that shouldn't be committed.
- `src/resources/` — icons/images used by the GUI.

**Designed for extension** — keep new features from requiring rewrites of existing modules:
- Persistence/access history/user login -> new module under `src/core/`, not bolted onto the GUI.
- Additional NFC readers, camera, facial recognition -> new modules under `src/hardware/`, following the same event pattern as the existing NFC reader module.
- API/network/Wi-Fi/web reporting -> a module that consumes `core`'s existing events rather than a parallel access-control path.
