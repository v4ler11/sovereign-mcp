import asyncio

import uvicorn
import uvloop

from core.app import App
from core.globals import LOGS_DIR, PORT
from core.logger import init_logger, info


def main():
    init_logger(LOGS_DIR)
    info("Logger initialized")

    app = App()

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=PORT,
        loop="uvloop",
        timeout_keep_alive=600,
        log_config=None,
        access_log=False,
        lifespan="on",
    )

    server = uvicorn.Server(config)

    try:
        server.run()
    except KeyboardInterrupt:
        info("KeyboardInterrupt handled")

    exit(0)
