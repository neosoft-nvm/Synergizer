# Changelog

## 0.1.0 preview — 2026-10-23

- Native Windows/Linux GUI with system, dark and light themes; tray controls and
  per-user desktop/application-menu shortcut installation.
- Computer canvas with full-edge grid layouts, add/edit/remove, validation,
  confirmed Apply, layout snapshots and restore.
- Import existing fixed-role Synergy layouts and use a shared dual-boot desk.
- Register public fingerprints for both desktop OSs without sharing private keys.
- Discover SSH candidates, verify host identity, pair Linux receivers, and try
  trusted alternate addresses. Private pairing keys remain local to each OS.
- Connection status, sharing logs/diagnostic export and reconnect controls.
- Managed client process supervision and recovery after prolonged disconnection.
- Windows/Linux CI archives with bundled Python/Qt, checksums and license notices.
- User, recovery, development and verification guides; include them in future builds.

Synergy 3 remains separately installed/activated. This preview does not manage
individual physical monitors, wake sleeping PCs, repair OS freezes, or remotely
provision Windows receivers. See [verification status](docs/STATUS.md) for tested
behavior and outstanding device checks.
