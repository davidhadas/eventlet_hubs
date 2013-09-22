import sys
from eventlet import patcher
from eventlet.hubs.hub import READ, WRITE, noop
from eventlet.hubs.poll import EXC_MASK, READ_MASK, WRITE_MASK
from eventlet.hubs.poll import Hub as _pollHub
from eventlet.hubs.epolls import Hub as _epollHub
from eventlet.hubs.selects import BAD_SOCK
from eventlet.hubs.selects import Hub as _selectHub
from eventlet.support import get_errno, clear_sys_exc_info
select = patcher.original('select')
time = patcher.original('time')
sleep = time.sleep

# The code here is based on the eventlet hubs code with slight modifications
class selectHub(_selectHub):
    def wait(self, seconds=None):
        readers = self.listeners[READ]
        writers = self.listeners[WRITE]
        if not readers and not writers:
            if seconds:
                time.sleep(seconds)
            return
        while True: 
            try:
                r, w, er = select.select(readers.keys(), writers.keys(), readers.keys() + writers.keys(), seconds)
            except select.error, e:
                if get_errno(e) == errno.EINTR:
                    seconds = 0
                    continue
                elif get_errno(e) in BAD_SOCK:
                    self._remove_bad_fds()
                    seconds = 0
                    continue
                else:
                    raise

            for fileno in er:
                readers.get(fileno, noop).cb(fileno)
                writers.get(fileno, noop).cb(fileno)
            
            if len(r) == 0 and len(w) == 0:
                return 

            for listeners, events in ((readers, r), (writers, w)):
                for fileno in events:
                    try:
                        listeners.get(fileno, noop).cb(fileno)
                    except self.SYSTEM_EXCEPTIONS:
                        raise
                    except:
                        self.squelch_exception(fileno, sys.exc_info())
                        clear_sys_exc_info()
            seconds = 0


def pollwait(self, seconds=None):
    readers = self.listeners[READ]
    writers = self.listeners[WRITE]
    SYSTEM_EXCEPTIONS = self.SYSTEM_EXCEPTIONS

    if not readers and not writers:
        if seconds:
            sleep(seconds)
        return
    while True:
        try:
            presult = self.do_poll(seconds)
        except (IOError, select.error), e:
            if get_errno(e) == errno.EINTR:
                seconds = 0
                continue
            raise
        if len(presult) == 0:
            return

        if self.debug_blocking:
            self.block_detect_pre()

        for fileno, event in presult:
            try:
                if event & READ_MASK:
                    readers.get(fileno, noop).cb(fileno)
                if event & WRITE_MASK:
                    writers.get(fileno, noop).cb(fileno)
                if event & select.POLLNVAL:
                    self.remove_descriptor(fileno)
                    continue
                if event & EXC_MASK:
                    readers.get(fileno, noop).cb(fileno)
                    writers.get(fileno, noop).cb(fileno)
            except SYSTEM_EXCEPTIONS:
                raise
            except:
                self.squelch_exception(fileno, sys.exc_info())
                clear_sys_exc_info()

        if self.debug_blocking:
            self.block_detect_post()
        seconds = 0

class pollHub(_pollHub):
    pass

class epollHub(_epollHub):
    pass

epollHub.wait = pollwait
pollHub.wait = pollwait
