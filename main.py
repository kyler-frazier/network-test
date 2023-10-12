import logging
import time
import asyncio
from urllib.parse import urlparse

from aiohttp import ClientSession, ClientTimeout
from prometheus_client import start_http_server, Counter, Histogram, utils

LOGGER = logging.getLogger("PacketLoss")
WEBSITES = ["https://www.google.com", "https://www.cloudflare.com", "https://www.att.com"]
CLIENT_TIMEOUT_SEC = 2
PING_INTERVAL = 1

call_metrics = Counter("call_count", "Times call failed", ["website", "status"])
call_duration_metrics = Histogram(
    "call_duration_seconds",
    "Time spent in call",
    ["website"],
    buckets=[0.0] + [round(i*(10**mag), 6) for mag in range(-3,2) for i in range(1,10)] + [utils.INF],
)
client_session = None


def setup_sync():
    logging.basicConfig(level=logging.INFO)
    LOGGER.info("Setting up...")
    start_http_server(8080)

async def setup_async():
    global client_session
    client_session = ClientSession(timeout=ClientTimeout(total=CLIENT_TIMEOUT_SEC))

async def ping(website: str):
    async with client_session.post(url=website) as _:
        pass

async def ping_handler(website: str):
    website_domain = urlparse(website).netloc
    start_time = time.time()
    try:
        call_metrics.labels(website=website_domain, status="start").inc()
        await ping(website)
        call_metrics.labels(website=website_domain, status="success").inc()
    except Exception as e:
        LOGGER.error(f"Error for ping: {e}")
        call_metrics.labels(website=website_domain, status="fail").inc()

    end_time = time.time()
    time_diff = end_time - start_time
    LOGGER.info(f"Time diff of {round(time_diff, 3)} on {website_domain}")
    call_duration_metrics.labels(website=website_domain).observe(time_diff)

async def runner():
    await setup_async()
    LOGGER.info("Running pinger...")
    while True:
        for website in WEBSITES:
            asyncio.create_task(ping_handler(website))
        await asyncio.sleep(PING_INTERVAL)

def main():
    setup_sync()
    asyncio.run(runner())


if __name__ == "__main__":
    main()
