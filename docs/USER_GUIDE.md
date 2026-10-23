# Synergizer user guide

Applies to the 0.1.0 preview. For installation, see the [README](../README.md).

## Open the app

Use **Synergizer** on your desktop or in the application menu/Windows Start menu.
The window can be closed without stopping configured keyboard sharing. The tray
icon belongs to the open app; closing it also removes that icon. Sharing and its
background recovery run separately.

Install the app before using **Set up sharing** so startup points to its installed
location. Merely installing shortcuts does not configure a new Synergy system.

## First setup on a new desk

1. Install and activate Synergy 3 on every computer. Open it once, complete initial
   setup, and enable encryption. Keep Synergy installed.
2. On the desktop with the physical keyboard and mouse, import an existing layout
   through **Settings → Import existing desk**, or add computers on **My desk**.
   The first tile is primary; later tiles are receivers.
3. Choose **Settings → Set up sharing on this computer**, select **Share this
   computer’s keyboard and mouse**, and choose a stable screen name. The desktop
   uses the same screen name in both operating systems.
4. Enter reachable desktop addresses in Settings. For dual boot, include addresses
   for both OS installations if they differ. Stable network addresses or names
   help avoid later connection problems.
5. Configure receivers using the instructions below, arrange their tiles, and
   choose **Apply changes**. Read and confirm the preview before applying.

Sharing setup backs up the original settings and replaces Synergy's normal layout
management/startup with managed sharing at sign-in. Do not run competing Synergy
layout managers. If the existing fixed-role setup is detected, it is imported;
you do not need to run setup again just to move a tile.

## Keep Windows and Linux in sync

1. Choose one folder on a drive both desktop operating systems can read and write.
2. In **Settings**, select that same physical folder from each OS. Its displayed
   path can differ between Windows and Linux.
3. Use the same stable primary screen name on both OSs. Configure sharing on each
   OS if it does not already have a working fixed-role setup.
4. Visit/select the shared folder on both OSs before pairing new Linux receivers.
   This registers both public desktop TLS fingerprints. Private certificate keys
   remain on their original OS. If a certificate changes later, register it and
   run receiver connection setup again to update trust.
5. On the desktop, apply the desired layout to save it into the shared folder.
   Managed startup loads that layout on the next boot. Existing fixed Windows
   tasks must use the layout in the selected shared folder.
6. Sign in to each OS and physically test the mouse and keyboard on all receivers.

The shared folder contains layout/profile data and public server fingerprints.
It is not a live network synchronization service. Mount/unlock the drive before
sharing starts. If sync cannot load it, startup keeps the last local layout;
Apply refuses an unavailable shared directory. Private pairing credentials are
per-OS: pair from each OS if you want its remote setup/reconnect controls to work.

## Move a computer or physical monitor

For a computer that moves to another side of the desk, drag its tile to an adjacent
empty grid position, then choose **Apply changes** and confirm. Keep every tile
connected to the group; gaps, overlaps and unsupported links are rejected.

For another monitor attached to the **same** computer, change that computer's OS
display settings. Do not create a second Synergizer tile for the monitor. Moving
or replacing a monitor does not change which computer shares the keyboard.

## Add a Linux laptop

1. Install/activate Synergy 3, enable encryption, enable SSH, install Python 3,
   and sign in to its graphical desktop. The preview expects the engine at
   `/opt/Synergy/synergy-core` and configuration in `~/.config/Synergy`.
2. Use **Find computers** or **Add computer**. Discovery lists SSH candidates;
   it does not prove they have Synergy or authorize access.
3. Enter a friendly name, unique Synergy screen name, reachable address(es),
   Linux platform, and the laptop's SSH username. Place its tile next to the group.
4. On **Computers**, choose **Set up connection**. Compare the SSH fingerprint
   with the laptop's host key before trusting it. An unexpected changed key needs
   investigation. Enter its SSH password once, or leave it blank for existing
   key access. The wizard then enrolls a local app-specific key.
5. Confirm setup, return to **My desk**, and **Apply changes**. Test input on it.

A friendly-name edit does not change the Synergy screen identity. Replacing a
receiver with a new identity requires removing and adding its tile. Changing the
primary identity requires matching sharing setup, not simply editing its label.

## Add a Windows receiver

Add its tile and screen name on the primary desktop. On the receiver itself,
install Synergizer and use **Settings → Set up sharing on this computer →
Receive keyboard and mouse from the desktop**. Match its screen name to the tile
and supply the desktop address. Encryption/trust must also be valid in its
Synergy setup; the remote Linux wizard does not provision Windows trust.
Apply the desktop layout and test input. This receiver path has not been
physically verified on the user's Windows device.

## Remove a computer

Select its tile, choose **Remove**, then **Apply changes**. Move the remaining
tiles together if removing one leaves a gap. The primary cannot be removed.
Removing a tile does not uninstall software, stop that receiver's service, or
revoke its SSH pairing key. A removed receiver may continue trying to reconnect.

## Undo and backups

**Undo** discards unapplied edits. After changes have been applied, Undo opens
**Backups**: select a recovery point and choose **Restore selected backup**.
Restore creates another backup and briefly restarts sharing. **Create backup now**
is also available. These restore layout/core/profile files, not an entire machine
or SSH trust/keys. Sharing-setup backups are separate; see troubleshooting.

## Share the utility

Share the platform archive and its matching SHA-256 checksum, not your installed
app-data folder. Recipients extract/open the app and install their own shortcuts.
They need their own installed, activated Synergy 3. No Python installation is
needed for the packaged GUI; a remotely configured Linux laptop still needs Python.

Exported desk profiles include device names, addresses and usernames. Sharing logs
may also identify devices. Review them before sending them to someone else.
