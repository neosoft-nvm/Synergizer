# Third-party components

Synergizer includes Python, Qt/PySide6, Paramiko, Cryptography, PyNaCl, and their
runtime dependencies in its portable packages. Each retains its own license.
PyInstaller preserves Python package metadata/licenses when supplied by upstream
hooks. Qt/PySide license texts are copied into THIRD-PARTY-LICENSES when available.

PySide6/Qt are dynamically linked; the unpacked `_internal` directory contains
replaceable libraries, not a statically linked proprietary Qt build. Upstream:
https://code.qt.io/pyside/pyside-setup.git and https://code.qt.io/qt/qtbase.git.
Qt and PySide are available under LGPLv3 or their other upstream license options.
The included notices identify those options; Synergizer's code is MIT licensed.

No Synergy executable, certificate, private key, account, or license is bundled.
Synergy and Symless names belong to their respective owners. This project is an
independent companion and is not affiliated with or endorsed by Symless.
