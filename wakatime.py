""" ==========================================================
File:        wakatime.py
Description: Wing IDE plugin for metrics about your programming.
Maintainer:  WakaTime <support@wakatime.com>
License:     BSD, see LICENSE for more details.
Website:     https://wakatime.com/
==========================================================="""


__version__ = '0.0.1'


import wingapi

import json
import logging
import os
import platform
import sys
import time
from subprocess import Popen, STDOUT, PIPE
try:
    import Queue as queue  # py2
except ImportError:
    import queue  # py3


logger = logging.getLogger('wakatime')


is_py2 = (sys.version_info[0] == 2)
is_py3 = (sys.version_info[0] == 3)

if is_py2:
    def u(text):
        if text is None:
            return None
        if isinstance(text, unicode):  # noqa: F821
            return text
        try:
            return text.decode('utf-8')
        except:
            try:
                return text.decode(sys.getdefaultencoding())
            except:
                try:
                    return unicode(text)  # noqa: F821
                except:
                    try:
                        return text.decode('utf-8', 'replace')
                    except:
                        try:
                            return unicode(str(text))  # noqa: F821
                        except:
                            return unicode('')  # noqa: F821

elif is_py3:
    def u(text):
        if text is None:
            return None
        if isinstance(text, bytes):
            try:
                return text.decode('utf-8')
            except:
                try:
                    return text.decode(sys.getdefaultencoding())
                except:
                    pass
        try:
            return str(text)
        except:
            return text.decode('utf-8', 'replace')

else:
    raise Exception('Unsupported Python version: {0}.{1}.{2}'.format(
        sys.version_info[0],
        sys.version_info[1],
        sys.version_info[2],
    ))


# globals
HEARTBEAT_FREQUENCY = 2
EDITOR_VERSION = wingapi.gApplication.GetProductInfo()[0]
LAST_HEARTBEAT = {
    'time': 0,
    'file': None,
}
HEARTBEATS = queue.Queue()


def _set_timeout(callback, seconds):
    """Runs the callback after the given seconds delay.

    If this is Sublime Text 3, runs the callback on an alternate thread. If this
    is Sublime Text 2, runs the callback in the main thread.
    """

    wingapi.gApplication.InstallTimeout(seconds * 1000, callback)


def _resources_folder():
    return os.path.join(os.path.expanduser('~'), '.wakatime')


def _architecture():
    arch = platform.machine() or platform.processor()
    if arch == 'armv7l':
        return 'arm'
    if arch == 'aarch64':
        return 'arm64'
    if 'arm' in arch:
        return 'arm64' if sys.maxsize > 2**32 else 'arm'
    return 'amd64' if sys.maxsize > 2**32 else '386'


def _cliLocation():
    osname = platform.system().lower()
    binary = 'wakatime-cli-{osname}-{arch}{ext}'.format(
        osname=osname,
        arch=_architecture(),
        ext='.exe' if osname == 'windows' else '',
    )
    return os.path.join(_resources_folder(), binary)


def _config_file():
    home = os.environ.get('WAKATIME_HOME')
    if home:
        return os.path.join(os.path.expanduser(home), '.wakatime.cfg')

    return os.path.join(os.path.expanduser('~'), '.wakatime.cfg')


def _obfuscate_apikey(command_list):
    cmd = list(command_list)
    apikey_index = None
    for num in range(len(cmd)):
        if cmd[num] == '--key':
            apikey_index = num + 1
            break
    if apikey_index is not None and apikey_index < len(cmd):
        cmd[apikey_index] = 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXX' + cmd[apikey_index][-4:]
    return cmd


def _should_track(filename, timestamp, is_write):
    last_file = LAST_HEARTBEAT['file']
    if filename != last_file or _enough_time_passed(timestamp, is_write):
        return True
    return False


def _enough_time_passed(timestamp, is_write):
    if timestamp - LAST_HEARTBEAT['time'] > HEARTBEAT_FREQUENCY * 60:
        return True
    if is_write and timestamp - LAST_HEARTBEAT['time'] > 2:
        return True
    return False


def _append_heartbeat(filename, timestamp, is_write, project):
    global LAST_HEARTBEAT

    project_name = None
    if project:
        project_name = os.path.basename(project.GetFilename()).rstrip('.wpr')

    # add this heartbeat to queue
    heartbeat = {
        'entity': filename,
        'timestamp': timestamp,
        'is_write': is_write,
        'cursorpos': None,
        'project': project_name,
    }
    HEARTBEATS.put_nowait(heartbeat)

    # make this heartbeat the LAST_HEARTBEAT
    LAST_HEARTBEAT = {
        'file': filename,
        'time': timestamp,
    }

    # process the queue of heartbeats in the future
    seconds = 4
    _set_timeout(_process_queue, seconds)


def _process_queue():
    global LAST_HEARTBEAT

    try:
        heartbeat = HEARTBEATS.get_nowait()
    except queue.Empty:
        return

    has_extra_heartbeats = False
    extra_heartbeats = []
    try:
        while True:
            extra_heartbeats.append(HEARTBEATS.get_nowait())
            has_extra_heartbeats = True
    except queue.Empty:
        pass

    thread = SendHeartbeatsThread(heartbeat)
    if has_extra_heartbeats:
        thread.add_extra_heartbeats(extra_heartbeats)
    thread.start()

    return None  # prevent this timeout from repeating


class SendHeartbeatsThread(object):

    def __init__(self, heartbeat):
        self.heartbeat = heartbeat
        self.has_extra_heartbeats = False

    def add_extra_heartbeats(self, extra_heartbeats):
        self.has_extra_heartbeats = True
        self.extra_heartbeats = extra_heartbeats

    def start(self):
        self.send_heartbeats()

    def build_heartbeat(self, entity=None, timestamp=None, is_write=None,
                        cursorpos=None, project=None):
        """Returns a dict for passing to wakatime-cli as arguments."""

        heartbeat = {
            'entity': entity,
            'timestamp': timestamp,
            'is_write': is_write,
        }

        if project:
            heartbeat['alternate_project'] = project

        if cursorpos is not None:
            heartbeat['cursorpos'] = '{0}'.format(cursorpos)

        return heartbeat

    def send_heartbeats(self):
        heartbeat = self.build_heartbeat(**self.heartbeat)
        ua = 'wing/{editor_version} wing-wakatime/{plugin_version}'.format(
            editor_version=EDITOR_VERSION,
            plugin_version=__version__,
        )
        cmd = [
            _cliLocation(),
            '--entity', heartbeat['entity'],
            '--time', str('%f' % heartbeat['timestamp']),
            '--plugin', ua,
        ]
        if heartbeat['is_write']:
            cmd.append('--write')
        if heartbeat.get('alternate_project'):
            cmd.extend(['--alternate-project', heartbeat['alternate_project']])
        if heartbeat.get('cursorpos') is not None:
            cmd.extend(['--cursorpos', heartbeat['cursorpos']])
        if self.has_extra_heartbeats:
            cmd.append('--extra-heartbeats')
            stdin = PIPE
            extra_heartbeats = [self.build_heartbeat(**x) for x in self.extra_heartbeats]
            extra_heartbeats = json.dumps(extra_heartbeats)
        else:
            extra_heartbeats = None
            stdin = None

        logger.info(' '.join(_obfuscate_apikey(cmd)))
        try:
            process = Popen(cmd, stdin=stdin, stdout=PIPE, stderr=STDOUT)
            inp = None
            if self.has_extra_heartbeats:
                inp = "{0}\n".format(extra_heartbeats)
                inp = inp.encode('utf-8')
            output, err = process.communicate(input=inp)
            output = u(output)
            retcode = process.poll()
            logger.info(retcode)
            if retcode:
                msg = 'wakatime-cli exited with status: {0}'.format(retcode)
                if retcode == 102:
                    logger.warn(msg)
                else:
                    logger.error(msg)
            if output:
                logger.error(u('wakatime-cli output: {0}').format(output))
        except:
            logger.error(u(sys.exc_info()[1]))


def _handle_activity(is_write):
    document = wingapi.gApplication.GetActiveEditor().GetDocument()
    if document:
        filename = document.GetFilename()
        timestamp = time.time()
        if _should_track(filename, timestamp, is_write):
            project = wingapi.gApplication.GetProject()
            _append_heartbeat(filename, timestamp, is_write, project)


def _on_selection_changed(start, end):
    _handle_activity(False)
    return None


def _on_saved(cacheFile):
    _handle_activity(True)
    return None


def _setup_signals():
    try:
        wingapi.gApplication.GetActiveEditor().connect('selection-changed', _on_selection_changed)
        wingapi.gApplication.GetActiveEditor().fSingletons.fGuiMgr.GetActiveDocument().fCache.connect('write-completed', _on_saved)
    except AttributeError:
        _set_timeout(_setup_signals, 1)
    return None


def _init(plugin_id):
    logger.info('Initializing WakaTime plugin v{ver}'.format(ver=__version__))
    wingapi.gApplication.EnablePlugin(plugin_id, True)

    _setup_signals()

    logger.info('Finished initializing WakaTime plugin.')
    return True


_plugin = ['WakaTime', _init]
