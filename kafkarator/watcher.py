import asyncio
import logging

from k8s.watcher import Watcher

from .background import DaemonThread

LOG = logging.getLogger()


class CrdWatcher(DaemonThread):
    def __init__(self, loop, model, event_handler):
        super().__init__(loop)
        self._watcher = Watcher(model)
        self._event_handler = event_handler

    def __call__(self):
        for event in self._watcher.watch():
            LOG.info("Received event %r", event)
            asyncio.run_coroutine_threadsafe(self._event_handler(event), self._loop)
