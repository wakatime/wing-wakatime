# -*- coding: utf-8 -*-
"""
    WakaTime Plugin Installer for Wing IDE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Downloads and installs the WakaTime Plugin for Wing IDE, Personal, 101.
    :copyright: (c) 2017 Alan Hamlett.
    :license: BSD, see LICENSE for more details.
"""


import contextlib
import os
import platform
import sys
from zipfile import ZipFile
try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen


PY2 = (sys.version_info[0] == 2)
ROOT_URL = 'https://raw.githubusercontent.com/wakatime/wing-wakatime/master/'
WAKATIME_CLI_URL = 'https://github.com/wakatime/wakatime/archive/master.zip'
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIRS = []
if platform.system() == 'Windows':
    CONFIG_DIRS.append(os.path.join(os.getenv('APPDATA'), 'Wing IDE 6', 'scripts'))
    CONFIG_DIRS.append(os.path.join(os.getenv('APPDATA'), 'Wing IDE 6.0', 'scripts'))
    CONFIG_DIRS.append(os.path.join(os.getenv('APPDATA'), 'Wing Personal 6.0', 'scripts'))
    CONFIG_DIRS.append(os.path.join(os.getenv('APPDATA'), 'Wing Personal 6', 'scripts'))
    CONFIG_DIRS.append(os.path.join(os.getenv('APPDATA'), 'Wing 101 6', 'scripts'))
    CONFIG_DIRS.append(os.path.join(os.getenv('APPDATA'), 'Wing 101 6.0', 'scripts'))
    RESOURCES_FOLDER = os.path.join(os.getenv('APPDATA'), 'WakaTime')
else:
    CONFIG_DIRS.append(os.path.join(os.path.expanduser('~'), '.wingide6', 'scripts'))
    CONFIG_DIRS.append(os.path.join(os.path.expanduser('~'), '.wingpersonal6', 'scripts'))
    CONFIG_DIRS.append(os.path.join(os.path.expanduser('~'), '.wing101-6', 'scripts'))
    RESOURCES_FOLDER = os.path.join(os.path.expanduser('~'), '.wakatime')
FILE = 'wakatime.py'


if PY2:
    import codecs
    open = codecs.open
    input = raw_input


def main():

    # download wakatime-cli
    if not os.path.exists(RESOURCES_FOLDER):
        os.mkdir(RESOURCES_FOLDER)
    zip_content = download(WAKATIME_CLI_URL)
    zip_file = os.path.join(RESOURCES_FOLDER, 'wakatime-master.zip')
    with open(zip_file, 'wb') as fh:
        fh.write(zip_content)
    with contextlib.closing(ZipFile(zip_file)) as zf:
        zf.extractall(RESOURCES_FOLDER)
    try:
        os.remove(zip_file)
    except:
        pass

    # download plugin
    contents = get_file_contents(FILE)
    if not contents:
        return

    # add plugin to config folders
    for folder in CONFIG_DIRS:
        if os.path.exists(os.path.dirname(folder)):
            if not os.path.exists(folder):
                os.mkdir(folder)
            save_file(os.path.join(folder, FILE), contents)

    print('Installed. You may now restart Wing.')
    if platform.system() == 'Windows':
        input('Press [Enter] to exit...')


def get_file_contents(filename):
    """Get file contents from local clone or GitHub repo."""

    if os.path.exists(os.path.join(SRC_DIR, filename)):
        with open(os.path.join(SRC_DIR, filename), 'r', encoding='utf-8') as fh:
            return fh.read()
    else:
        url = ROOT_URL + filename
        return download(url)


def download(url):
    """Get file contents from remote url."""

    resp = urlopen(url)
    return resp.read()


def save_file(filename, contents):
    """Saves contents to filename."""

    with open(filename, 'w', encoding='utf-8') as fh:
        fh.write(contents)


if __name__ == '__main__':
    main()
