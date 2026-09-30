# Changelog

Reconstructed from the original development history (February - May 2026).

## [Unreleased]
- Fixed: Password Generator returned the user's PowerShell profile banner instead of a password; it now uses Python's `secrets` module
- Fixed: all `powershell -Command` calls now use `-NoProfile`, so profile output no longer pollutes results and commands start faster
- Security: dialog input (hosts, package IDs, user names, passwords, drive letters, extensions, ports, Wi-Fi names) is validated before being placed in a shell command
- Fixed: status box strips ANSI colour codes and is updated thread-safely via the Tk main loop
- Changed: bare `except:` clauses replaced with `except Exception:`

## [4.0 "Pro Suite"] - 2026-05-05
- AppForge, CyberScan and BackupPro launchers built in (now optional companion projects)
- Complete Windows Update repair and Defender repair
- 3,400+ lines, dark-mode UI

## [V30] - 2026-02-10
- "400 commands" edition with AI helper menu

## [V25] - 2026-02-10
- Python conversion of the original PowerShell toolkit; enhanced dark mode UI, Windows 11 fixes

## [Original]
- PowerShell `TechniciansToolkit.ps1`
