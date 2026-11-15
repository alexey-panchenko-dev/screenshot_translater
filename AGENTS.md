# Screen Translator project rules

## Scope

- This repository contains a Windows 10/11 desktop application written for Python 3.12+.
- Keep the application local-only: no backend, accounts, telemetry, or cloud storage.
- Implement work phase by phase. Do not start a later phase until the current phase runs and its checks pass.
- The current milestone is **Phase 1 — Capture**.

## Architecture

- Keep UI, capture, OCR, translation, storage, and orchestration in separate modules.
- Put central workflow orchestration in `core/pipeline.py`.
- External OCR and translation providers must implement the small interfaces in their respective `base.py` modules.
- Do not put business logic in Qt widgets or in `main.py`.
- Prefer the simplest reliable Windows-native solution. Avoid unnecessary abstractions and dependencies.

## Code quality

- Target Python 3.12 or newer and use type hints.
- Use small functions and descriptive names. Avoid global mutable state and God classes.
- Log technical failures; never expose tracebacks or secrets to users.
- Never commit `.env`, API keys, logs, screenshots, databases, build output, or virtual environments.
- Add or update focused tests for non-visual logic with every phase.

## UI and concurrency

- Never run OCR, HTTP calls, or SQLite work in the Qt UI thread.
- Qt objects must only be touched from their owning thread.
- A repeated capture replaces pending work; do not build an unbounded queue.
- Preserve correct global screen coordinates and initialize Windows DPI awareness before `QApplication`.

## Verification

- Run `pytest` after meaningful changes.
- Run Ruff when available.
- For capture/UI changes, document a short Windows manual test because automated tests cannot validate global hotkeys or compositor behavior.
- Explain any newly added dependency in the phase summary.

