# Verification status

Last reviewed: **2026-10-23**. Version: **0.1.0 preview**.
This is a dated verification record, not a live health dashboard.

## Confirmed

- Before the new GUI was installed, the user physically verified the fixed-role
  sharing setup on both desktop Windows and Fedora with both Linux laptops.
- The native Fedora Synergizer UI and desktop icon were seen and accepted by the
  user. The final update was then installed and reopened.
- A live equivalent-layout Apply completed on Fedora with a backup, and both
  laptop TCP connections were present afterward. Final installation checks also
  found the sharing service active and both connections present.
- Read-only trusted SSH access to both existing Linux laptops succeeded.
- GitHub Actions run **40038738404** passed **31 tests** and frozen offscreen UI
  rendering on Windows and Linux for app commit `9157e3a`.
- Both final preview archives had matching SHA-256 checksums and included Qt
  license notices. They were checked for known private-profile/certificate/key
  files and the paid Synergy engine; those were not bundled.

## Still pending

- The final Windows GUI is staged for the user's next Windows sign-in. A one-time
  setup launcher is prepared to install shortcuts and open it. The user has not
  yet confirmed this first launch, icons, or a layout edit from that Windows UI.
- The new Windows GUI must not be described as device-verified based only on CI.
  Earlier successful Windows sharing tests establish the existing sharing setup.
- Broader fresh-install, Windows receiver, Linux distribution/session, and repeated
  suspend/resume testing remain preview validation work.
- The Fedora laptop's previous OS freeze has no confirmed root cause. Recovery
  helpers can restart a stalled client; they cannot prevent or fix an OS freeze.

## Distribution

Source is on GitHub. A v0.1.0 preview release with Windows/Linux archives and
checksums is prepared as an **unpublished draft**. Publish only when authorized.
The code ships without user-specific addresses, SSH accounts, credentials, or
licenses. Personal deployment details stay outside the public repository.

The documentation update following `9157e3a` changes guidance and ensures future
packages contain these guides. Previously built archives remain the verified
`9157e3a` snapshots; their embedded README is older. Updated guides are supplied
beside the shared packages and in this repository. Do not silently replace an
archive without also regenerating its checksum and recording its build.

## Next acceptance check

1. Boot Windows and sign in.
2. Confirm Synergizer opens and Desktop/Start menu shortcuts exist.
3. Move the mouse desktop → middle laptop → left laptop and back; type on both.
4. Verify the same arrangement after returning to Fedora.
5. Record the user's result here; do not infer acceptance from process/socket state.
