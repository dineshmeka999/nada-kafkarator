import asyncio
import logging

from fastapi import FastAPI, Depends, HTTPException
from fiaas_logging import init_logging
from k8s import config as k8s_config
from prometheus_client import Gauge
from starlette_exporter import PrometheusMiddleware, handle_metrics

from kafkarator.config import K8sSettings, LogSettings
from kafkarator.models import Topic
from kafkarator.watcher import CrdWatcher

app = FastAPI()
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)

TEST_GAUGE = Gauge("thread_gauge", "Shows the number of alive background threads")
BACKGROUND_THREADS = []


# TODO: Move to separate module when implementing real handler
async def test_handler(event):
    logging.info("Handling event: %s", event)


@app.on_event("startup")
async def configure_logging():
    log_settings = LogSettings()
    init_logging(format=log_settings.format)


@app.on_event("startup")
def configure_k8s():
    k8s_settings = K8sSettings()
    k8s_config.api_server = k8s_settings.api_server
    k8s_config.api_token = k8s_settings.api_token.data
    if k8s_settings.api_cert.path:
        k8s_config.verify_ssl = k8s_settings.api_cert.path
    if k8s_settings.client_cert.path:
        k8s_config.cert = (k8s_settings.client_cert.path, k8s_settings.client_key.path)


@app.on_event("startup")
async def start_watchers():
    topic_watcher = CrdWatcher(asyncio.get_event_loop(), Topic, test_handler)
    topic_watcher.start()
    BACKGROUND_THREADS.append(topic_watcher)


@app.get("/")
async def root():
    return "Hello World"


def is_alive():
    dead_threads = [t.name for t in BACKGROUND_THREADS if not t.is_alive()]
    TEST_GAUGE.set(len(BACKGROUND_THREADS) - len(dead_threads))
    if not all(t.is_alive() for t in BACKGROUND_THREADS):
        dead_threads = [t.name for t in BACKGROUND_THREADS if not t.is_alive()]
        raise HTTPException(status_code=500, detail="These threads are not alive: {}".format(dead_threads))
    return True


@app.get("/isHealthy")
async def is_healthy(is_alive: bool = Depends(is_alive)):
    return "OK" if is_alive else "NOPE"


@app.get("/isReady")
async def is_ready(is_alive: bool = Depends(is_alive)):
    return "OK" if is_alive else "NOPE"


if __name__ == "__main__":
    import pathlib
    from hypercorn.config import Config
    from hypercorn.asyncio import serve

    config_path = pathlib.Path(__file__).parent.parent.joinpath("hypercorn_config.py")
    config = Config.from_pyfile(config_path)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(serve(app, config))
