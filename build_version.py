"""Generate PyInstaller and Inno Setup version resources from version.json.

Usage:
    python build_version.py --bump    # increment build, then generate
    python build_version.py           # generate without changing version
"""
import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "version.json"


def atomic_write(path: Path, data: str):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(data, encoding='utf-8')
    os.replace(tmp, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bump', action='store_true', help='Increment build number before generating')
    args = parser.parse_args()

    state = json.loads(STATE.read_text(encoding='utf-8'))
    nums = [state[key] for key in ('major', 'minor', 'build')]
    if any(type(n) is not int or n < 0 or n > 65535 for n in nums):
        parser.error('major/minor/build must be integers between 0 and 65535')
    if args.bump:
        if state['build'] == 65535:
            parser.error('build number limit reached; increment minor and reset build')
        state['build'] += 1
        atomic_write(STATE, json.dumps(state, indent=2, ensure_ascii=False) + '\n')

    major, minor, build = (state[k] for k in ('major', 'minor', 'build'))
    version = f'{major}.{minor}.{build}'
    version4 = f'{version}.0'
    atomic_write(ROOT / 'version_info.txt', f'''VSVersionInfo(
  ffi=FixedFileInfo(filevers=({major},{minor},{build},0), prodvers=({major},{minor},{build},0),
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0,0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('CompanyName', 'DPI Changer'),
    StringStruct('FileDescription', 'DPI Changer'),
    StringStruct('FileVersion', '{version4}'),
    StringStruct('InternalName', 'DPIChanger'),
    StringStruct('OriginalFilename', 'DPI Changer.exe'),
    StringStruct('ProductName', 'DPI Changer'),
    StringStruct('ProductVersion', '{version4}')
  ])]), VarFileInfo([VarStruct('Translation', [1033, 1200])])]
)
''')
    atomic_write(ROOT / 'version.iss', f'#define MyAppVersion "{version}"\n')
    print(f'Version: {version}')


if __name__ == '__main__':
    main()
