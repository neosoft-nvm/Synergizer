# Synergizer

Keep user-facing replies short and concrete.

Native PySide6 desktop app; source is in synergizer/.
This is a Synergy 3 companion, not a replacement input-sharing engine.
The desktop remains the server across its Windows/Fedora installations.
Never bundle a user's license, certificate/private key, addresses, or profile.

Development:
- .venv/bin/python -m synergizer
- QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests -v
- .venv/bin/python scripts/build.py
- .venv/bin/python scripts/smoke.py

Windows packages must be built on Windows. The build workflow handles both OSs.
Preserve Qt's replaceable dynamic libraries and third-party license notices.

Live changes must use validation, backup, atomic writes, restart, and rollback.
Do not silently discard unsupported layout sections or partial/wrapping links.
SSH host trust requires an explicit fingerprint confirmation; no auto-accept.
The pairing password is transient; an app key is stored only on the local OS.
Keep source/render/packaged/native-device verification boundaries explicit.

The old background-only setup is imported automatically. Existing recovery/tray
helpers must remain intact when merely changing the desktop layout.

Documentation:
- Keep README.md, docs/USER_GUIDE.md, docs/TROUBLESHOOTING.md,
  docs/DEVELOPMENT.md, docs/STATUS.md and CHANGELOG.md aligned with behavior.
- Record device acceptance separately from CI and process/socket observations.
- Keep personal deployment details out of public docs. Include guides/notices in
  packages; never replace release archives without updating checksums/build records.
