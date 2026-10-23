# Synergizer

**Your desk. Seamlessly connected.**

A native Windows/Linux companion for Synergy 3: visually arrange computers,
keep a dual-boot desktop in one place, reconnect sharing, and undo layout changes.

## What you can do
- Drag computers left, right, above, or below each other on a snapping desk canvas.
- Add, rename, remove, discover, and configure receiving Linux computers over trusted SSH.
- Import your existing Synergy layout; preview and apply changes with an automatic backup.
- Keep a common desk profile on a drive accessible to both Windows and Linux.
- View connection status, reconnect clients, inspect logs, and restore a saved desk.
- Choose system/light/dark appearance. Desktop and application-menu shortcuts are included.

## Install and share
Download a package from this repository's **Actions → Build desktop packages** run.

**Windows:** extract the ZIP, open its Synergizer folder, and double-click
`Install Synergizer.cmd`. A desktop and Start menu shortcut will be created.
The portable `Synergizer.exe` also runs directly. Unsigned preview builds may
show Windows' normal reputation prompt.

**Linux:** extract the archive, open the Synergizer folder and run `install.sh`.
This installs per-user, without root, and creates desktop/application-menu launchers.
Synergizer can also run directly from the extracted folder. Linux packages from
GitHub build on Ubuntu 22.04; a locally built package requires a compatible host.

Synergy 3 must be installed and activated separately on every computer. Its paid
engine and your license are **not** included. Remote Linux setup requires Python 3,
a reachable SSH service, and a verified SSH host key. The pairing wizard accepts
a password once or uses an existing SSH key, then authorizes an app-specific key.
Windows protects that private key with DPAPI; Linux stores it in a private user folder. Windows receivers can be
configured locally through Settings → Set up sharing. Native Windows remote setup
is not available in this preview.

## Dual boot
Choose the same shared folder from Settings on Windows and Linux. Use a drive
both operating systems can read and write. Synergizer keeps passwords, private
keys, certificates, and licenses out of that shared profile. Select the same
stable desktop screen name in both operating systems. The shared layout is
loaded before sharing starts when configured through Synergizer.

The existing fixed-role setup created before this app is automatically imported.
On Linux, installing the application adds a pre-start shared-layout sync hook.
On Windows, an existing fixed desktop task uses the layout in its shared folder;
choose that folder in Settings. Apply changes updates that layout immediately.

## Current boundaries
The layout editor supports a connected grid with full-edge links. Complex
partial-edge, wrapping, or alias layouts are refused rather than silently lost.
Each tile is a computer. Arrange individual monitors in your OS display settings.
Discovery scans at most a local /24 network for SSH candidates; discovery is not
pairing. An unknown host key or missing key authorization is surfaced, not bypassed.
The app does not wake a suspended computer or repair a frozen operating system.

Receiving clients configured through Synergizer have process supervision and
recovery after 90 seconds disconnected. Your pre-existing recovery timer and tray
control remain in place when you only edit a desktop layout. Offline receiving
computers keep retrying. Layout Apply does not require every laptop to be online.

## Development
Python 3.12+ and PySide6 are required.

```sh
python -m pip install -e .
python -m synergizer
python -m unittest discover -s tests -v
python -m pip install pyinstaller==6.22.3
python scripts/build.py
```

Build Windows packages on Windows and Linux packages on Linux. The GitHub Actions
workflow builds both and uploads downloadable archives with SHA-256 checksums.
Each package bundles Python and Qt, so recipients do not need to install Python.
Synergizer's code is MIT licensed. Bundled Qt/PySide libraries retain their LGPL
licenses and notices, included by the packaging tool. Synergizer is independent
of and not endorsed by Symless.
