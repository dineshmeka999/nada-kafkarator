import asyncio
import logging
from threading import Thread


class DaemonThread(Thread):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        super(DaemonThread, self).__init__(None, self._logging_target, self._make_name())
        self.daemon = True
        self._loop = loop

    def _logging_target(self):
        log = logging.getLogger()
        try:
            while True:
                try:
                    self()
                except Exception:
                    log.exception("Error in background thread %s, persisting", self.name)
        except BaseException:
            log.critical("Fatal error in background thread %s, giving up", self.name, exc_info=True)

    def _make_name(self):
        return self.__class__.__name__

    def __call__(self):
        raise NotImplementedError("Subclass must implement this method")
