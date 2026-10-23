# Synergizer

**Your desk. Seamlessly connected.**

A native Windows/Linux companion for Synergy 3. Arrange computers visually,
keep a dual-boot desktop in one place, reconnect sharing, and restore saved layouts.
**Version 0.1.0 is a preview.** Synergy 3 must be installed and activated separately
on every computer; its engine and your license are not bundled.

## Start here

- [User guide](docs/USER_GUIDE.md): install, dual boot, move/add/remove computers.
- [Troubleshooting](docs/TROUBLESHOOTING.md): reconnect, suspend/resume, backups.
- [Development](docs/DEVELOPMENT.md): architecture, storage, tests and packaging.
- [Verification status](docs/STATUS.md): tested behavior and remaining checks.
- [Changelog](CHANGELOG.md) and [third-party notices](THIRD_PARTY.md).

## Install

Preview packages are available to signed-in GitHub users from a successful
[Build desktop packages run](https://github.com/neosoft-nvm/Synergizer/actions/workflows/build.yml).
Download the appropriate workflow artifact and extract its enclosed package.
A v0.1.0 release has been prepared as an **unpublished draft**; it is not yet a
public release download. Packages can also be shared directly with recipients.

**Windows:** extract `Synergizer-0.1.0-Windows-x64.zip`, open its `Synergizer`
folder, and run `Synergizer.exe`. In **Settings**, choose **Install desktop and
menu shortcuts**, then open the installed shortcut. `Install Synergizer.cmd`
is an alternative. Unsigned preview builds may show a Windows reputation prompt.

**Linux:** extract `Synergizer-0.1.0-Linux-x64.tar.gz`, open its `Synergizer`
folder, and launch `Synergizer`. Choose **Settings → Install desktop and menu
shortcuts**, then open the installed shortcut. `install.sh` is an alternative.
Installation is per-user; some desktops require marking the launcher trusted.

Python and Qt are included in packages. Linux CI builds on Ubuntu 22.04;
compatibility still depends on the target's system libraries and desktop session.
Windows packages are built on Windows. See [verification status](docs/STATUS.md)
before treating build success as device compatibility.

## What it does

- Drag computer tiles onto a connected grid; preview, apply, and restore layouts.
- Keep one desktop screen name across Windows/Linux, using a shared writable drive.
- Discover SSH candidates and configure receiving Linux computers through trusted SSH.
- Show connection status, reconnect sharing, and export sharing logs.
- Offer system, light and dark themes, tray controls, and desktop/menu shortcuts.

Each tile represents **one computer**, not an individual physical monitor. Arrange
individual displays using Windows/Linux display settings. The editor supports
full-edge grid links; partial-edge, wrapping and alias layouts are refused.
Sharing starts after sign-in. Synergizer cannot wake a sleeping computer or fix an
OS freeze. Remote Linux setup requires Python 3, SSH, a logged-in desktop session,
and the expected Synergy installation paths. Remote Windows setup is not included.

## Develop

Python 3.12+:

```sh
python -m pip install -e .
python -m synergizer
```

See [development instructions](docs/DEVELOPMENT.md) for tests and packages.
Synergizer is MIT licensed. Bundled components retain their own licenses.
This project is independent of and not endorsed by Symless.
