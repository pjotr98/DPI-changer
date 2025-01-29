import os
import json
import subprocess
from pystray import Icon, Menu, MenuItem
from PIL import Image

# Шляхи до файлів
APPDATA_PATH = os.path.join(os.getenv("LOCALAPPDATA"), "DPI Changer")
CONFIG_FILE = os.path.join(APPDATA_PATH, "config.cfg")
ICON_FILE = os.path.join(APPDATA_PATH, "icon.ico")
LOCALE_FILE = os.path.join(APPDATA_PATH, "locales.json")

# Доступні варіанти DPI
AVAILABLE_DPI = [100, 125, 150, 175]

# Переконуємося, що папка існує
os.makedirs(APPDATA_PATH, exist_ok=True)

def load_locales():
    """Завантажує локалізовані рядки з JSON-файлу."""
    if os.path.exists(LOCALE_FILE):
        with open(LOCALE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Завантаження локалізації
locales = load_locales()

def load_config():
    """Завантажити конфігурацію з файлу."""
    default_config = {"dpi_values": [100, 125], "selected_dpi": 125, "language": "en"}
    
    if not os.path.exists(CONFIG_FILE):
        save_config(default_config)
        return default_config

    config = {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            key, value = line.strip().split("=")
            if key == "dpi_values":
                config[key] = [int(x.strip()) for x in value.split(",") if x.strip().isdigit()]
            elif key == "selected_dpi":
                config[key] = int(value.strip())
            else:
                config[key] = value.strip()

    return config

def save_config(config):
    """Зберегти конфігурацію у файл"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(f"dpi_values={','.join(map(str, sorted(config['dpi_values'])))}\n")
        f.write(f"selected_dpi={config['selected_dpi']}\n")
        f.write(f"language={config['language']}\n")

# Завантаження конфігурації
config = load_config()
dpi_values = config["dpi_values"]
selected_dpi = config["selected_dpi"]
current_locale = config["language"]

def t(key, **kwargs):
    """Отримати локалізований текст для поточної мови."""
    return locales.get(current_locale, {}).get(key, key).format(**kwargs)

def toggle_dpi(icon, item=None):
    """Перемикання DPI між вибраними значеннями"""
    global selected_dpi
    current_index = dpi_values.index(selected_dpi)
    new_dpi = dpi_values[(current_index + 1) % len(dpi_values)]
    set_dpi(icon, new_dpi)

def set_dpi(icon, dpi):
    """Змінює DPI на вибране значення"""
    global selected_dpi
    selected_dpi = dpi
    config["selected_dpi"] = dpi
    save_config(config)
    
    command = f"powershell.exe -Command Set-DisplayScale -DisplayId 1 -Scale {dpi}"
    subprocess.run(command, shell=True)
    icon.notify(t("notify_dpi_changed", dpi=dpi))
    update_menu(icon)  # Оновлення меню

def toggle_dpi_option(icon, dpi_value):
    """Додає або видаляє DPI з доступних значень та оновлює `config.cfg`"""
    global dpi_values
    dpi_value = int(str(dpi_value))
    dpi_values = [d for d in dpi_values if isinstance(d, int)]
    if dpi_value in dpi_values:
        if len(dpi_values) > 1:
            dpi_values.remove(dpi_value)
    else:
        dpi_values.append(dpi_value)
        dpi_values.sort()
    config["dpi_values"] = dpi_values
    save_config(config)
    update_menu(icon)

def switch_language(icon, lang_code):
    """Перемикає мову та оновлює меню"""
    global current_locale
    current_locale = lang_code
    config["language"] = current_locale
    save_config(config)
    icon.notify(t("notify_language_switched"))
    icon.title = t("tray_title")
    update_menu(icon)

def update_menu(icon):
    """Оновити меню після зміни мови або налаштувань"""
    icon.menu = Menu(
        MenuItem(t("menu_toggle_dpi"), toggle_dpi, default=True),
        MenuItem(t("menu_configure_dpi"), Menu(
            *(MenuItem(f"{dpi}", lambda icon, dpi_value=dpi: toggle_dpi_option(icon, int(str(dpi_value))),
                      checked=lambda item, dpi_value=dpi: int(str(dpi_value)) in dpi_values) for dpi in AVAILABLE_DPI)
        )),
        MenuItem(t("menu_language"), Menu(
            MenuItem(t("menu_language_english"), lambda icon: switch_language(icon, "en")),
            MenuItem(t("menu_language_ukrainian"), lambda icon: switch_language(icon, "uk")),
        )),
        MenuItem(t("menu_exit"), lambda icon: icon.stop()),
    )

def load_icon():
    """Завантажуємо іконку з правильного шляху."""
    if os.path.exists(ICON_FILE):
        return Image.open(ICON_FILE)
    else:
        print(f"⚠ Warning: icon.ico не знайдено за шляхом {ICON_FILE}")
        return None

icon = Icon(t("tray_title"), load_icon(), menu=None)
update_menu(icon)
icon.run()
