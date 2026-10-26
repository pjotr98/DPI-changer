"""DPI Changer: Windows tray utility, Python standard library only.

Run: pythonw dpi_tray_app_stdlib.py
CLI: python dpi_tray_app_stdlib.py --list | --set 125 [--monitor primary|DISPLAY2]
The DPI set/get interface (-3/-4) is undocumented by Microsoft.
"""
import argparse
import json
import ctypes as c
from ctypes import wintypes as w
import os
from pathlib import Path
import sys

if sys.platform != 'win32':
    raise SystemExit('Windows only')

user32 = c.WinDLL('user32', use_last_error=True)
gdi32 = c.WinDLL('gdi32', use_last_error=True)
shell32 = c.WinDLL('shell32', use_last_error=True)
kernel32 = c.WinDLL('kernel32', use_last_error=True)

SCALES = (100, 125, 150, 175, 200, 225, 250, 300, 350, 400, 450, 500)
# In installed builds, editable files live alongside DPI Changer.exe.
FROZEN = getattr(sys, 'frozen', False)
BASEDIR = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent
BUNDLE_DIR = Path(getattr(sys, '_MEIPASS', BASEDIR))

CONFIG = BASEDIR / 'config.cfg'
LOCALES = BASEDIR / 'locales.json'
# Bundled icon is a fallback only; translations/config remain external and editable.
ICON = BASEDIR / 'icon.ico'
if not ICON.is_file():
    ICON = BUNDLE_DIR / 'icon.ico'

# Old field names are interpreted only for backward compatibility.
LOCALE_KEY_MAP = {
    'tray_title': 'title', 'menu_toggle_dpi': 'toggle',
    'menu_configure_dpi': 'scales', 'menu_language': 'language',
    'menu_exit': 'exit', 'notify_dpi_changed': 'dpi_changed',
    'notify_language_switched': 'language_switched',
    'menu_monitor': 'monitor', 'menu_primary': 'primary',
    'menu_set_scale': 'set', 'menu_toggle_values': 'scales',
    'error_dpi_changed': 'error',
}


def load_locales():
    """All translated UI text comes from external locales.json."""
    source = json.loads(LOCALES.read_text(encoding='utf-8-sig'))
    if not isinstance(source, dict) or 'en' not in source:
        raise ValueError(f'{LOCALES}: expected JSON object with en translations')
    result = {}
    for lang, items in source.items():
        if not isinstance(items, dict) or not isinstance(lang, str):
            raise ValueError(f'{LOCALES}: invalid language {lang!r}')
        entry = {LOCALE_KEY_MAP.get(k, k): v for k, v in items.items() if isinstance(v, str)}
        entry.setdefault('language_name', lang)
        result[lang] = entry
    return result


MESSAGES = load_locales()

# ctypes Win32 declarations: pointer-sized handles, 32-bit Windows DWORDs.
LRESULT = c.c_ssize_t
WNDPROC = c.WINFUNCTYPE(LRESULT, w.HWND, w.UINT, w.WPARAM, w.LPARAM)
MONITORENUMPROC = c.WINFUNCTYPE(w.BOOL, w.HMONITOR, w.HDC, c.POINTER(w.RECT), w.LPARAM)

class MONITORINFOEXW(c.Structure):
    _fields_ = [('cbSize', w.DWORD), ('rcMonitor', w.RECT), ('rcWork', w.RECT),
                ('dwFlags', w.DWORD), ('szDevice', w.WCHAR * 32)]

class LUID(c.Structure):
    _fields_ = [('LowPart', w.DWORD), ('HighPart', w.LONG)]

class OPENADAPTER(c.Structure):
    _fields_ = [('DeviceName', w.WCHAR * 32), ('hAdapter', w.UINT),
                ('AdapterLuid', LUID), ('VidPnSourceId', w.UINT)]

class CLOSEADAPTER(c.Structure):
    _fields_ = [('hAdapter', w.UINT)]

class DPIHEADER(c.Structure):
    _fields_ = [('type', c.c_int32), ('size', w.UINT),
                ('adapterId', LUID), ('id', w.UINT)]

class DPIGET(c.Structure):
    _fields_ = [('header', DPIHEADER), ('minScaleRel', c.c_int32),
                ('curScaleRel', c.c_int32), ('maxScaleRel', c.c_int32)]

class DPISET(c.Structure):
    _fields_ = [('header', DPIHEADER), ('scaleRel', c.c_int32)]

class WNDCLASSW(c.Structure):
    _fields_ = [('style', w.UINT), ('lpfnWndProc', WNDPROC), ('cbClsExtra', c.c_int),
                ('cbWndExtra', c.c_int), ('hInstance', w.HINSTANCE), ('hIcon', w.HICON),
                ('hCursor', w.HANDLE), ('hbrBackground', w.HBRUSH),
                ('lpszMenuName', w.LPCWSTR), ('lpszClassName', w.LPCWSTR)]

class GUID(c.Structure):
    _fields_ = [('Data1', w.DWORD), ('Data2', w.WORD), ('Data3', w.WORD),
                ('Data4', c.c_ubyte * 8)]

class NOTIFYICONDATAW(c.Structure):
    _fields_ = [('cbSize', w.DWORD), ('hWnd', w.HWND), ('uID', w.UINT),
                ('uFlags', w.UINT), ('uCallbackMessage', w.UINT), ('hIcon', w.HICON),
                ('szTip', w.WCHAR * 128), ('dwState', w.DWORD), ('dwStateMask', w.DWORD),
                ('szInfo', w.WCHAR * 256), ('uTimeoutOrVersion', w.UINT),
                ('szInfoTitle', w.WCHAR * 64), ('dwInfoFlags', w.DWORD),
                ('guidItem', GUID), ('hBalloonIcon', w.HICON)]

class POINT(c.Structure):
    _fields_ = [('x', w.LONG), ('y', w.LONG)]

class MSG(c.Structure):
    _fields_ = [('hwnd', w.HWND), ('message', w.UINT), ('wParam', w.WPARAM),
                ('lParam', w.LPARAM), ('time', w.DWORD), ('pt', POINT),
                ('lPrivate', w.DWORD)]

# Explicit prototypes protect pointer/handle values on 64-bit Python.
def proto(dll, name, restype, *args):
    fn = getattr(dll, name)
    fn.restype = restype
    fn.argtypes = list(args)
    return fn

EnumDisplayMonitors = proto(user32, 'EnumDisplayMonitors', w.BOOL, w.HDC, c.c_void_p, MONITORENUMPROC, w.LPARAM)
GetMonitorInfoW = proto(user32, 'GetMonitorInfoW', w.BOOL, w.HMONITOR, c.POINTER(MONITORINFOEXW))
OpenAdapter = proto(gdi32, 'D3DKMTOpenAdapterFromGdiDisplayName', w.LONG, c.POINTER(OPENADAPTER))
CloseAdapter = proto(gdi32, 'D3DKMTCloseAdapter', w.LONG, c.POINTER(CLOSEADAPTER))
GetDPI = proto(user32, 'DisplayConfigGetDeviceInfo', w.LONG, c.POINTER(DPIGET))
SetDPI = proto(user32, 'DisplayConfigSetDeviceInfo', w.LONG, c.POINTER(DPISET))
RegisterClassW = proto(user32, 'RegisterClassW', w.ATOM, c.POINTER(WNDCLASSW))
CreateWindowExW = proto(user32, 'CreateWindowExW', w.HWND, w.DWORD, w.LPCWSTR, w.LPCWSTR,
                         w.DWORD, c.c_int, c.c_int, c.c_int, c.c_int,
                         w.HWND, w.HMENU, w.HINSTANCE, c.c_void_p)
DefWindowProcW = proto(user32, 'DefWindowProcW', LRESULT, w.HWND, w.UINT, w.WPARAM, w.LPARAM)
DestroyWindow = proto(user32, 'DestroyWindow', w.BOOL, w.HWND)
PostQuitMessage = proto(user32, 'PostQuitMessage', None, c.c_int)
GetMessageW = proto(user32, 'GetMessageW', w.BOOL, c.POINTER(MSG), w.HWND, w.UINT, w.UINT)
TranslateMessage = proto(user32, 'TranslateMessage', w.BOOL, c.POINTER(MSG))
DispatchMessageW = proto(user32, 'DispatchMessageW', LRESULT, c.POINTER(MSG))
Shell_NotifyIconW = proto(shell32, 'Shell_NotifyIconW', w.BOOL, w.DWORD, c.POINTER(NOTIFYICONDATAW))
CreatePopupMenu = proto(user32, 'CreatePopupMenu', w.HMENU)
AppendMenuW = proto(user32, 'AppendMenuW', w.BOOL, w.HMENU, w.UINT, c.c_size_t, w.LPCWSTR)
DestroyMenu = proto(user32, 'DestroyMenu', w.BOOL, w.HMENU)
TrackPopupMenu = proto(user32, 'TrackPopupMenu', w.UINT, w.HMENU, w.UINT,
                       c.c_int, c.c_int, c.c_int, w.HWND, c.c_void_p)
GetCursorPos = proto(user32, 'GetCursorPos', w.BOOL, c.POINTER(POINT))
SetForegroundWindow = proto(user32, 'SetForegroundWindow', w.BOOL, w.HWND)
PostMessageW = proto(user32, 'PostMessageW', w.BOOL, w.HWND, w.UINT, w.WPARAM, w.LPARAM)
LoadImageW = proto(user32, 'LoadImageW', w.HANDLE, w.HINSTANCE, w.LPCWSTR, w.UINT,
                   c.c_int, c.c_int, w.UINT)
LoadIconW = proto(user32, 'LoadIconW', w.HICON, w.HINSTANCE, c.c_void_p)
GetModuleHandleW = proto(kernel32, 'GetModuleHandleW', w.HMODULE, w.LPCWSTR)
MessageBoxW = proto(user32, 'MessageBoxW', c.c_int, w.HWND, w.LPCWSTR, w.LPCWSTR, w.UINT)
DestroyIcon = proto(user32, 'DestroyIcon', w.BOOL, w.HICON)


def monitors():
    found = []
    @MONITORENUMPROC
    def callback(handle, hdc, rect, extra):
        info = MONITORINFOEXW()
        info.cbSize = c.sizeof(info)
        if GetMonitorInfoW(handle, c.byref(info)):
            found.append({'device': info.szDevice, 'primary': bool(info.dwFlags & 1),
                          'width': info.rcMonitor.right - info.rcMonitor.left,
                          'height': info.rcMonitor.bottom - info.rcMonitor.top})
        return True
    if not EnumDisplayMonitors(None, None, callback, 0):
        raise c.WinError(c.get_last_error())
    return sorted(found, key=lambda item: (not item['primary'], item['device']))


def selected_monitor(config):
    available = monitors()
    if not available:
        raise RuntimeError('No active monitors')
    pref = config.get('monitor', 'primary').upper()
    if pref != 'PRIMARY':
        match = next((m for m in available if m['device'].upper().endswith('\\' + pref)
                      or m['device'].upper() == pref), None)
        if match:
            return match
    return next((m for m in available if m['primary']), available[0])


def query_dpi(device, scale=None):
    adapter = OPENADAPTER()
    adapter.DeviceName = device
    status = OpenAdapter(c.byref(adapter))
    if status:
        raise OSError(f'OpenAdapter({device}) NTSTATUS=0x{status & 0xffffffff:08X}')
    try:
        packet = DPIGET()
        packet.header = DPIHEADER(-3, c.sizeof(packet), adapter.AdapterLuid, adapter.VidPnSourceId)
        status = GetDPI(c.byref(packet))
        if status:
            raise OSError(f'Get DPI ({device}) Win32 error={status}')
        recommended = -packet.minScaleRel
        current_index = recommended + packet.curScaleRel
        current = SCALES[current_index] if 0 <= current_index < len(SCALES) else None
        possible = [SCALES[i] for i in range(len(SCALES))
                    if packet.minScaleRel <= i - recommended <= packet.maxScaleRel]
        if scale is not None:
            if scale not in possible:
                raise ValueError(f'{scale}% not supported by {device}; available: {possible}')
            request = DPISET()
            request.header = DPIHEADER(-4, c.sizeof(request), adapter.AdapterLuid, adapter.VidPnSourceId)
            request.scaleRel = SCALES.index(scale) - recommended
            status = SetDPI(c.byref(request))
            if status:
                raise OSError(f'Set DPI ({device}) Win32 error={status}')
        return current, possible
    finally:
        status = CloseAdapter(c.byref(CLOSEADAPTER(adapter.hAdapter)))
        if status:
            print(f'Warning: CloseAdapter status=0x{status & 0xffffffff:08X}', file=sys.stderr)


def load_config():
    result = {'dpi_values': [100, 125], 'selected_dpi': 125, 'language': 'en', 'monitor': 'primary'}
    if CONFIG.exists():
        try:
            for line in CONFIG.read_text(encoding='utf-8-sig').splitlines():
                if '=' not in line:
                    continue
                key, raw = line.split('=', 1)
                key, raw = key.strip(), raw.strip()
                if key == 'dpi_values':
                    values = sorted(set(int(x) for x in raw.split(',') if x.strip().isdigit()) & set(SCALES))
                    if values:
                        result[key] = values
                elif key == 'selected_dpi' and raw.isdigit() and int(raw) in SCALES:
                    result[key] = int(raw)
                elif key == 'language' and raw in MESSAGES:
                    result[key] = raw
                elif key == 'monitor' and raw:
                    result[key] = raw
        except (OSError, UnicodeError):
            pass
    return result


def save_config(cfg):
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    lines = [f'dpi_values={",".join(map(str, cfg["dpi_values"]))}',
             f'selected_dpi={cfg["selected_dpi"]}', f'language={cfg["language"]}',
             f'monitor={cfg["monitor"]}']
    CONFIG.write_text('\n'.join(lines) + '\n', encoding='utf-8')


class TrayApp:
    WM_TRAY = 0x8001
    WM_APP_RESTART = 0x8002
    WM_RBUTTONUP = 0x0205
    WM_LBUTTONUP = 0x0202
    WM_NULL = 0
    MF_STRING = 0
    MF_POPUP = 0x10
    MF_SEPARATOR = 0x800
    MF_CHECKED = 0x08
    MF_GRAYED = 0x01
    TPM_RETURNCMD = 0x100

    def __init__(self):
        self.cfg = load_config()
        if self.cfg['language'] not in MESSAGES:
            self.cfg['language'] = 'en'
        self.hwnd = None
        self.actions = {}
        self.counter = 100
        self.title = 'DPI Changer'
        self.wndproc_ref = WNDPROC(self.wndproc)
        self.nid = NOTIFYICONDATAW()
        self.taskbar_created = proto(user32, 'RegisterWindowMessageW', w.UINT, w.LPCWSTR)('TaskbarCreated')

    def t(self, key, **params):
        language = MESSAGES.get(self.cfg['language'], MESSAGES['en'])
        template = language.get(key, MESSAGES['en'].get(key))
        if template is None:
            raise KeyError(f'Missing localization key: {key} in {LOCALES}')
        return template.format(**params)

    def error(self, ex):
        MessageBoxW(self.hwnd, str(ex), self.t('error'), 0x10)

    def change(self, scale):
        try:
            target = selected_monitor(self.cfg)
            query_dpi(target['device'], scale)
            self.cfg['selected_dpi'] = scale
            save_config(self.cfg)
            self.balloon(self.t('dpi_changed', dpi=scale))
        except (OSError, ValueError, RuntimeError) as ex:
            self.error(ex)

    def toggle(self):
        try:
            target = selected_monitor(self.cfg)
            current, supported = query_dpi(target['device'])
            choices = [x for x in self.cfg['dpi_values'] if x in supported]
            if not choices:
                raise ValueError(f'No configured scales supported on {target["device"]}')
            new = choices[(choices.index(current) + 1) % len(choices)] if current in choices else choices[0]
            self.change(new)
        except (OSError, ValueError, RuntimeError) as ex:
            self.error(ex)

    def balloon(self, text):
        self.nid.uFlags = 0x01 | 0x02 | 0x04 | 0x10
        self.nid.szInfoTitle = self.t('title')
        self.nid.szInfo = text[:255]
        self.nid.dwInfoFlags = 0x01
        Shell_NotifyIconW(1, c.byref(self.nid))

    def add(self, menu, label, fn=None, checked=False, disabled=False, submenu=None):
        if submenu is not None:
            AppendMenuW(menu, self.MF_POPUP, submenu, label)
        else:
            self.counter += 1
            flags = self.MF_STRING | (self.MF_CHECKED if checked else 0) | (self.MF_GRAYED if disabled else 0)
            AppendMenuW(menu, flags, self.counter, label)
            if fn and not disabled:
                self.actions[self.counter] = fn

    def submenu(self):
        return CreatePopupMenu()

    def show_menu(self):
        # Read translations again so editing locales.json needs no restart.
        global MESSAGES
        try:
            MESSAGES = load_locales()
        except (OSError, ValueError, UnicodeError) as exc:
            self.error(f'Unable to read {LOCALES}: {exc}')
            return
        if self.cfg['language'] not in MESSAGES:
            self.cfg['language'] = 'en'
        self.actions.clear()
        self.counter = 100
        main = self.submenu()
        try:
            entries = monitors()
            target = selected_monitor(self.cfg)
            try:
                current, supported = query_dpi(target['device'])
            except (OSError, ValueError) as ex:
                current, supported = None, []
            self.add(main, f'{self.t("toggle")} ({current or "?"}%)', self.toggle)

            scales = self.submenu()
            for percent in SCALES:
                self.add(scales, f'{percent}%', lambda v=percent: self.change(v),
                         checked=(current == percent), disabled=percent not in supported)
            self.add(main, self.t('set'), submenu=scales)

            targets = self.submenu()
            self.add(targets, self.t('primary'),
                     lambda: self.set_monitor('primary'), checked=self.cfg['monitor'] == 'primary')
            for m in entries:
                name = m['device'].split('\\')[-1]
                mark = ' ★' if m['primary'] else ''
                label = f'{name}{mark} ({m["width"]}x{m["height"]})'
                self.add(targets, label, lambda d=name: self.set_monitor(d),
                         checked=self.cfg['monitor'].upper() == name.upper())
            self.add(main, self.t('monitor'), submenu=targets)

            toggles = self.submenu()
            for percent in SCALES:
                self.add(toggles, f'{percent}%', lambda v=percent: self.toggle_option(v),
                         checked=percent in self.cfg['dpi_values'])
            self.add(main, self.t('scales'), submenu=toggles)
            langs = self.submenu()
            for code, translations in MESSAGES.items():
                title = translations.get('language_name', code)
                self.add(langs, title, lambda lang=code: self.set_language(lang),
                         checked=self.cfg['language'] == code)
            self.add(main, self.t('language'), submenu=langs)
            AppendMenuW(main, self.MF_SEPARATOR, 0, None)
            self.add(main, self.t('exit'), lambda: DestroyWindow(self.hwnd))
            pos = POINT()
            GetCursorPos(c.byref(pos))
            SetForegroundWindow(self.hwnd)
            cmd = TrackPopupMenu(main, self.TPM_RETURNCMD | 0x0002, pos.x, pos.y, 0, self.hwnd, None)
            PostMessageW(self.hwnd, self.WM_NULL, 0, 0)
            if cmd in self.actions:
                self.actions[cmd]()
        except (OSError, RuntimeError) as ex:
            self.error(ex)
        finally:
            DestroyMenu(main)

    def set_monitor(self, device):
        self.cfg['monitor'] = device
        save_config(self.cfg)

    def toggle_option(self, percent):
        values = set(self.cfg['dpi_values'])
        if percent in values and len(values) > 1:
            values.remove(percent)
        else:
            values.add(percent)
        self.cfg['dpi_values'] = sorted(values)
        save_config(self.cfg)

    def set_language(self, lang):
        if lang not in MESSAGES:
            return
        self.cfg['language'] = lang
        save_config(self.cfg)
        self.nid.szTip = self.t('title')
        self.nid.uFlags = 0x04
        Shell_NotifyIconW(1, c.byref(self.nid))
        self.balloon(self.t('language_switched'))

    def install_icon(self):
        self.nid.cbSize = c.sizeof(self.nid)
        self.nid.hWnd = self.hwnd
        self.nid.uID = 1
        self.nid.uCallbackMessage = self.WM_TRAY
        self.nid.uFlags = 0x01 | 0x02 | 0x04
        self.nid.hIcon = self.hicon
        self.nid.szTip = self.t('title')
        if not Shell_NotifyIconW(0, c.byref(self.nid)):
            raise c.WinError(c.get_last_error())

    def wndproc(self, hwnd, msg, wp, lp):
        if msg == self.WM_TRAY:
            if lp == self.WM_RBUTTONUP:
                self.show_menu()
            elif lp == self.WM_LBUTTONUP:
                self.toggle()
            return 0
        if msg == self.taskbar_created:
            self.install_icon()
            return 0
        if msg == 0x0002:  # WM_DESTROY
            Shell_NotifyIconW(2, c.byref(self.nid))
            if getattr(self, 'hicon', None):
                DestroyIcon(self.hicon)
            PostQuitMessage(0)
            return 0
        return DefWindowProcW(hwnd, msg, wp, lp)

    def run(self):
        instance = GetModuleHandleW(None)
        class_name = 'DPIChangerPythonStdlibTray'
        wc = WNDCLASSW()
        wc.lpfnWndProc = self.wndproc_ref
        wc.hInstance = instance
        wc.lpszClassName = class_name
        if not RegisterClassW(c.byref(wc)):
            raise c.WinError(c.get_last_error())
        self.hwnd = CreateWindowExW(0, class_name, self.title, 0,
                                    0, 0, 0, 0, None, None, instance, None)
        if not self.hwnd:
            raise c.WinError(c.get_last_error())
        # Load the actual ICO (small 16x16 frame for the notification area).
        # Do not silently substitute the generic application placeholder.
        if not ICON.is_file():
            raise FileNotFoundError(f'icon.ico not found: {BASEDIR} or {BUNDLE_DIR}')
        self.hicon = LoadImageW(None, str(ICON), 1, 16, 16, 0x10)
        if not self.hicon:
            raise c.WinError(c.get_last_error())
        self.install_icon()
        msg = MSG()
        while (status := GetMessageW(c.byref(msg), None, 0, 0)) > 0:
            TranslateMessage(c.byref(msg))
            DispatchMessageW(c.byref(msg))
        if status == -1:
            raise c.WinError(c.get_last_error())


def main():
    parser = argparse.ArgumentParser(description='Windows DPI Changer, no dependencies')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--list', action='store_true', help='List active monitors and current scaling')
    group.add_argument('--set', type=int, choices=SCALES, metavar='PERCENT', help='Set DPI scale')
    parser.add_argument('--monitor', default='primary', help='primary (default) or DISPLAY2')
    args = parser.parse_args()
    if args.list:
        for item in monitors():
            try:
                current, possible = query_dpi(item['device'])
                print(f'{item["device"]} {"PRIMARY" if item["primary"] else ""} '
                      f'{item["width"]}x{item["height"]}: {current}% available={possible}')
            except OSError as ex:
                print(f'{item["device"]}: {ex}')
    elif args.set is not None:
        m = selected_monitor({'monitor': args.monitor})
        query_dpi(m['device'], args.set)
        print(f'{m["device"]}: {args.set}%')
    else:
        TrayApp().run()


if __name__ == '__main__':
    main()
