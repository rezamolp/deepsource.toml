from __future__ import annotations

import asyncio
from aiohttp import web


async def health_handler(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def run_health_server(host: str, port: int) -> None:
    app = web.Application()
    app.add_routes([web.get("/healthz", health_handler)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()
    # Keep running
    while True:
        await asyncio.sleep(3600)
