import asyncio
from unittest import mock

import pytest
from k8s.base import Model, WatchEvent
from k8s.fields import Field
from k8s.watcher import Watcher

from kafkarator.watcher import CrdWatcher

EXAMPLE_NAME = "example1"

EXAMPLE_ADDED_EVENT = {
    "object": {
        "name": EXAMPLE_NAME
    },
    "type": WatchEvent.ADDED
}


class Example(Model):
    class Meta:
        watch_list_url_template = "/apis/example"

    name = Field(str)


class TestWatcher:
    @pytest.fixture
    def loop(self):
        return asyncio.SelectorEventLoop()

    @pytest.fixture
    def watcher(self):
        return mock.create_autospec(spec=Watcher, spec_set=True, instance=True)

    def test_calls_loop(self, loop, watcher):
        event = WatchEvent(EXAMPLE_ADDED_EVENT, Example)
        watcher.watch.return_value = [event]

        completer = loop.create_future()

        async def handler(e):
            completer.set_result(e)

        w = CrdWatcher(loop, Example, handler)
        w._watcher = watcher
        w()

        loop.call_later(5.0, lambda: loop.stop())
        loop.run_until_complete(completer)
        assert completer.done()
        assert completer.result() == event
