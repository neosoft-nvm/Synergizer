# Development and packaging

## Run and verify

Use Python 3.12+ in a virtual environment. From the repository:

```sh
python -m venv .venv
```

Activate `.venv/bin/activate` on Linux or `.venv\Scripts\Activate.ps1` in Windows
PowerShell, then:

```sh
python -m pip install -e .
python -m synergizer
python -m unittest discover -s tests -v
python -m pip install pyinstaller==6.22.3 pillow
python scripts/build.py
python scripts/smoke.py
```

For a headless Linux test/render, set `QT_QPA_PLATFORM=offscreen`. The CI workflow
sets it on both operating systems. Linux CI also installs `libegl1`, `libopengl0`,
`libxcb-cursor0`, and `libxkbcommon-x11-0`. Do not assume these are the complete
runtime requirements for every desktop distribution.

Use temporary data directories for UI experiments. `--data-dir` only redirects
Synergizer data, not the underlying real Synergy configuration paths. Do not
invoke sharing setup, Apply, or reconnect against real devices in a UI smoke test.

## Components

| File | Responsibility |
| --- | --- |
| `synergizer/ui.py` | QtWidgets canvas, navigation, dialogs, tray and background jobs |
| `synergizer/model.py` | Desk schema, parsing, validation and full-edge config generation |
| `synergizer/backend.py` | Import, snapshots, transactional layout application, sync, status |
| `synergizer/setup.py` | Local sharing startup/service migration |
| `synergizer/remote_setup.py` | Generated Linux receiver setup script |
| `synergizer/ssh_access.py` | Host verification, authentication and per-OS pairing keys |
| `synergizer/supervisor.py` | Engine process restart and disconnected-client recovery |
| `synergizer/install.py` | Per-user application copy and shortcuts |
| `scripts/build.py` | Native package archives, documentation, licenses and SHA-256 |
| `scripts/smoke.py` | Frozen executable render and packaged-file checks |

Apply validates the model, requires a configured primary, snapshots affected
files, writes replacements atomically, and restarts local sharing. On failure it
restores files and attempts another restart. This is not a distributed transaction
across devices; offline receivers need not be reachable to save a layout.

## Storage and startup

| Data | Linux | Windows |
| --- | --- | --- |
| Synergizer app data | `~/.local/share/Synergizer` | `%LOCALAPPDATA%\Synergizer` |
| Installed executable | `<app-data>/app/Synergizer` | `<app-data>\app\Synergizer.exe` |
| Original Synergy config | `~/.config/Synergy` | `%PROGRAMDATA%\Synergy\config` |
| Managed Synergy config | `~/.config/Synergy-DualBoot` | `%PROGRAMDATA%\Synergy-DualBoot` |
| Expected engine | `/opt/Synergy/synergy-core` | `%PROGRAMFILES%\Synergy\synergy-core.exe` |

App data includes `settings.json`, `desk.json`, layout backups, and local SSH
trust/key material. Private app keys use Windows DPAPI or Linux user-only file
permissions. Never put these files in the repository or distributable package.
The selected shared folder holds `desk.json`, `layout.conf` and
`server-identities.json` (public TLS fingerprints). Profiles include device names,
addresses and usernames; they are not anonymous.

Linux sharing uses the user unit `synergy-dualboot.service` and graphical-session
startup. Installing over an existing managed setup adds a `--sync` ExecStartPre
hook. New local Windows setup uses the interactive logon task `Synergizer Sharing`;
existing `Synergy Fixed Desktop` tasks can also be restarted by the backend.
Local setup pauses Synergy's normal manager. All input sharing here starts after
sign-in, not at the OS login screen.

CLI entry points: normal launch opens the UI; `--install` installs a frozen build;
`--sync` loads the shared desk; `--supervise` runs the sharing supervisor;
`--session-start` imports session variables/restarts sharing. UI automation can
use `--theme`, `--screenshot`, and `--data-dir`. See `python -m synergizer --help`.

## Build and distribute

Build on the target OS; PyInstaller does not cross-compile these packages.
`.github/workflows/build.yml` builds x64 Windows 2022 and Ubuntu 22.04 runners with
Python 3.12. It runs unit tests, builds, renders the frozen app, and uploads
archives/checksums. Current archive names contain version 0.1.0; update the build
script, package metadata and app version together when bumping versions.

Archives contain the `Synergizer/` folder, bundled runtime, install helper,
README, docs, changelog and license notices. Keep Qt/PySide dynamic libraries
replaceable and preserve `THIRD-PARTY-LICENSES`. See [notices](../THIRD_PARTY.md).
Verify SHA-256 and inspect archives for accidental credentials before sharing.
Never bundle Synergy's paid engine, a user's license, certificates or profiles.
A matching SHA-256 detects corruption; an unsigned checksum is not publisher
identity verification.

Workflow artifacts require GitHub access and expire under repository retention
settings. Publishing a GitHub release is a separate action; the build workflow
does not publish one. A release draft is not a public download.

## Verification boundaries

Unit tests cover models, layout transactions, identity sharing, pairing and UI
behavior. Frozen offscreen rendering checks packaged imports/resources. Neither
proves actual Windows input behavior, display-server compatibility, successful
resume after a real suspend, or a working physical keyboard/mouse path. Record
those device tests separately in [STATUS.md](STATUS.md).
