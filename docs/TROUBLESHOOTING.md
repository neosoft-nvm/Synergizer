# Troubleshooting

## A laptop does not reconnect after opening its lid

1. Wake it, sign in/unlock as required, and confirm its desktop responds locally.
2. Wait for Wi-Fi/network access to return. A sleeping/frozen OS cannot reconnect.
3. In Synergizer, refresh connection status. New managed clients restart after
   more than 90 seconds without a server connection, with polling/restart delays.
   This is recovery behavior, not a guaranteed time from opening the lid.
4. If needed, use **Computers → Reconnect** for a paired Linux receiver. This
   requires reachable SSH and trusted, authorized access on the current OS.
5. Use **Recovery → Show sharing logs** and export diagnostics if it still fails.

Legacy receivers keep their existing recovery timer/tray when only the layout is
edited; their timings may differ. If a laptop has frozen, preserve its system logs
before changing power settings. Restarting Synergy cannot diagnose or fix an OS
crash. Closing a lid does not remove the computer tile automatically.

## Sharing has stopped on the desktop

Use **Recovery → Reconnect this computer**. This restarts local managed sharing;
input to other computers can briefly stop. It does not remotely wake the laptops.
A desktop shown as Running means its service/process is running. Connected status
is based on TCP peers; confirm mouse and keyboard behavior physically as well.

If no managed sharing configuration/task exists, complete **Settings → Set up
sharing on this computer**. If encryption/trust errors appear, verify the server
certificate and receiver trust before pairing again.

## Windows uses the wrong layout after a dual boot

Verify the same physical shared folder is selected on both OSs, writable and
available at startup. Check the stable primary screen name matches each installed
sharing configuration. Apply the desired layout from the primary desktop.
Existing fixed Windows startup must reference that shared layout. An unavailable
shared drive leaves the last local layout in place; it cannot receive new edits.

## Discovery or SSH setup fails

Discovery probes SSH on port 22, on at most a local /24 plus known candidates.
It cannot find every network, sleeping machine, nonstandard SSH port, or computer
behind a blocking firewall. Add a reachable address manually if needed.

Check the username, SSH service, network, and host fingerprint. Trusted alternate
addresses can be tried, but untrusted/changed keys are not silently accepted.
Pair separately on Windows and Linux; private app keys are not shared between OSs.
Do not send passwords or private keys with a bug report.

## Layout rejected or a move did not take effect

Edits stay drafts until **Apply changes** is confirmed. Keep tiles adjacent and
connected without overlap. The preview cannot edit partial-edge/wrap/alias
configurations. Imported/exported profiles are layout drafts, not whole-system
backups. Use OS display settings for monitors attached to one computer.

If Apply fails, the app restores the saved files and attempts to restart the old
configuration. A second restart failure is possible; inspect logs and verify
sharing rather than assuming rollback restored a working service.

## Restore a previous layout

Open **Backups**, select a recovery point, and choose **Restore selected backup**.
The app snapshots the current files first. Keep backups local: they contain
machine paths and configuration. They do not restore certificates, SSH credentials,
startup services/tasks or original Synergy management.

One-time **local setup** separately copies the original/custom Synergy folders to
`<app-data>/setup-backups/<timestamp>/`. Remote Linux setup copies them to the
receiver's `~/.local/share/Synergizer/backups/<timestamp>/`. These setup snapshots
are not selectable layout recovery points in the Backups page. There is no GUI
command to undo an entire sharing setup or uninstall its startup service. Full
migration back to Synergy's manager requires restoring the relevant configuration
and disabling managed startup; deleting the GUI alone does not do this.

## Install or update shortcuts

Close the old Synergizer window before replacing an installed app, especially on
Windows. Extract the new package, open it, and choose **Settings → Install desktop
and menu shortcuts**. Open the installed shortcut afterward. Settings/backups are
outside `app/` and preserved when the application directory is replaced.

On Linux, the desktop may require **Allow Launching**/trusting the launcher. A
missing tray icon alone does not show that background sharing failed. Closing
Synergizer removes its tray icon but leaves configured sharing running.

## Reporting a problem

Include the OS/version, Synergizer version, Synergy version, whether this followed
a boot/resume/network change, and what works locally. Export sharing diagnostics
from Recovery and review names/addresses before sharing. Record physical input
results separately from connection status. Never attach certificates/private keys,
licenses, pairing keys, passwords or your whole app-data directory.
