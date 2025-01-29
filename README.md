# DPI Changer
# ![DPI Changer](https://raw.githubusercontent.com/pjotr98/DPI-changer/refs/heads/main/icon.ico)

## Overview👀
DPI Changer is a lightweight system tray application that allows users to quickly switch between predefined DPI scaling values on Windows. The application supports multiple DPI values and provides an easy way to configure them through a tray menu.

## Features🔍
- Easily toggle between predefined DPI values.
- Configure which DPI values are available via the tray menu.
- Supports localization (English & Ukrainian).
- Auto-starts with Windows.
- Uses `DisplayConfig` PowerShell module to change DPI settings.
- Custom tray icon.

## Installation🛠️
1. Download the latest `DPI_Changer_Installer.exe` from the [Releases](https://github.com/pjotr98/DPI-changer/releases) page.
2. Run the installer and follow the on-screen instructions.
3. The application will be installed in `%LOCALAPPDATA%\DPI Changer` and added to the Windows startup.
4. Ensure that the `DisplayConfig` PowerShell module is installed. The installer attempts to install it automatically.

## Usage.
1. Right-click the tray icon to open the menu.
2. Select **Toggle DPI** to switch between enabled DPI values.
3. Go to **Configure DPI** to enable or disable specific DPI values.
4. Change the language via **Language > English / Ukrainian**.
5. Exit the application using **Exit**.

## Uninstallation🗑️
1. Open **Settings > Apps & Features**.
2. Find **DPI Changer**, click **Uninstall**, and follow the prompts.
3. The uninstaller removes all files except configuration settings in `%LOCALAPPDATA%\DPI Changer`.
4. If necessary, manually remove the registry entry for auto-start: `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run\DPIChanger`.

## Contributing🔧
If you would like to contribute, feel free to fork the repository and submit a pull request.

## License🪪
This project is licensed under the MIT License.

## Credits👨‍💻🤖
Developed by Oleksandr Zheliazkov and Assistant Maryna (ChatGPT)

