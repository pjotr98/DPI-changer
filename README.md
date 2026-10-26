# DPI Changer

![DPI Changer](https://raw.githubusercontent.com/pjotr98/DPI-changer/refs/heads/main/icon.ico)

## What's New in 2.0 🚀

**DPI Changer 2.0 has been completely rewritten from the ground up.** The old PowerShell-based implementation and its dependency on the third-party `DisplayConfig` module are gone.

The app now communicates directly with Windows using native APIs through Python's built-in `ctypes` module. It also uses native Windows system tray functionality instead of `pystray` and Pillow. **No PowerShell scripts, external Python runtime packages, or separate DPI utilities are required to run the application.**

The rewrite brings multi-monitor support, a simpler one-click workflow, editable localization files, and a proper Windows installer.

## Overview 👀

DPI Changer is a lightweight Windows system tray application for quickly switching between predefined display scaling values. Click its tray icon to cycle through your preferred DPI scales, or right-click to choose a specific scale, monitor, or language.

## Features 🔍

- **One-click DPI switching:** Left-click the tray icon to cycle through your enabled scaling values.
- **Flexible scaling options:** Select the percentages used for cycling or set a specific supported scale from the context menu.
- **Multi-monitor support:** Select any active monitor, or leave the target on **Primary (automatic)** to follow your current main display.
- **Native Windows integration:** Direct Windows API calls through Python's standard-library `ctypes`; no PowerShell `DisplayConfig` module.
- **Dependency-free runtime:** No `pystray`, Pillow, or other third-party Python packages required by the app. The Windows executable bundles the Python runtime.
- **Custom tray icon and notifications.**
- **Extensible localization:** Language entries are loaded from an editable `locales.json`; contributors can add languages without changing the Python code.
- **Persistent settings:** DPI preferences, language, and selected monitor are stored in `config.cfg`.
- **Optional startup with Windows:** Available during installation.

> **Compatibility note:** DPI changes use undocumented Windows display configuration request types. They work on supported Windows configurations but are not guaranteed across all future Windows versions or display drivers.

## Installation 🛠️

1. Download the latest installer from [Releases](https://github.com/pjotr98/DPI-changer/releases).
2. Run the installer and follow the instructions.
3. DPI Changer installs by default to `%LOCALAPPDATA%\Programs\DPI Changer`.
4. Optionally enable **Start with Windows** during setup.

**No Python or PowerShell module installation is needed for users of the packaged app.**

## Usage 🖱️

1. **Left-click** the tray icon to switch to the next enabled DPI scale. After the last value, the cycle starts again.
2. **Right-click** the icon to open the settings menu.
3. Use **Set scale** to apply a specific supported value.
4. Use **Monitor** to target an available display, or choose **Primary (automatic)**.
5. Use **Toggle values** to choose the scales included in the left-click cycle.
6. Use **Language** to select a translation available in `locales.json`.
7. Use **Exit** to close the application.

## Configuration & Localization 🌍

The installed application uses these editable files next to `DPI Changer.exe`:

```text
%LOCALAPPDATA%\Programs\DPI Changer\
├── DPI Changer.exe
├── config.cfg
├── locales.json
└── icon.ico
```

Example `config.cfg`:

```ini
dpi_values=100,125,150
selected_dpi=125
language=en
monitor=primary
```

To add another language, edit `locales.json` and add an entry such as `"de": { "language_name": "Deutsch", ... }` following the existing English keys. The new language appears in the **Language** menu; reopening that menu reloads the translations. Missing translations fall back to English when available.

**Tip:** Restart DPI Changer after changing `config.cfg` manually, so the app reloads your saved settings. Keep a backup of personalized files before uninstalling.

## Build from Source 🧰

The application itself uses only Python's standard library. **PyInstaller and Inno Setup are build-time tools**, not dependencies for people who install the released executable.

Requirements for building on Windows:

- Python 3 and PyInstaller
- [Inno Setup 6](https://jrsoftware.org/isinfo.php) to produce an installer

Install PyInstaller and run the build script from the repository root:

```powershell
py -m pip install pyinstaller
.\build.bat
```

The build generates `dist\DPI Changer.exe`. If the Inno Setup command-line compiler (`ISCC.exe`) is available, it also builds an installer in `output\`. Otherwise, open `installer.iss` in Inno Setup and compile it manually.

Version information is managed through `version.json`; the build script generates the corresponding executable and installer version metadata.

## Uninstallation 🗑️

Open **Windows Settings → Apps → Installed apps**, locate **DPI Changer**, and choose **Uninstall**. Back up any customized `config.cfg` or `locales.json` before uninstalling; removal of installation files may also remove those customizations.

## Contributing 🔧

Contributions, bug reports, feature suggestions, and new translations are welcome! Feel free to fork the repository and submit a pull request.

## License 🪪

This project is licensed under the MIT License. See [LICENSE](LICENSE).

## Credits 👨‍💻🤖

Developed by Oleksandr Zheliazkov and Assistant Maryna (ChatGPT).
