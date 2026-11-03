"""Explicit opt-in scheduled discovery worker for single-operator deployment.

Run only in a dedicated process/container, not inside the FastAPI server.
SQLite lock stops overlaps. No activity unless AUTODISCOVERY_ENABLED=1.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import signal

from app.wishcatcher.discovery.pipeline import DiscoveryRunner

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s discovery %(message)s",
)
logger = logging.getLogger("wishcatcher.discovery")


def schedule_config() -> tuple[list[str], int, int, int]:
    names = [n.strip() for n in os.getenv(
        "WISHCATCHER_DISCOVERY_SOURCES", "hn_ask,hn_show").split(",") if n.strip()]
    if not names or any(name not in DiscoveryRunner.SUPPORTED for name in names):
        raise ValueError("Unsupported scheduled discovery source")
    interval = max(3600, min(int(os.getenv("WISHCATCHER_DISCOVERY_INTERVAL_SEC", "21600")), 86400))
    limit = max(1, min(int(os.getenv("WISHCATCHER_DISCOVERY_PER_SOURCE", "3")), 10))
    contexts = max(1, min(int(os.getenv("WISHCATCHER_DISCOVERY_MAX_CONTEXTS", "20")), 70))
    return names, interval, limit, contexts


async def main() -> None:
    if os.getenv("WISHCATCHER_AUTODISCOVERY_ENABLED", "0") != "1":
        logger.warning("Autodiscovery not enabled; worker exiting without any network requests")
        return
    names, interval, limit, contexts = schedule_config()
    logger.info("Scheduled sources=%s interval_s=%s limits=%s/%s",
                ",".join(names), interval, limit, contexts)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, stop.set)
        except (NotImplementedError, RuntimeError):
            pass
    while not stop.is_set():
        try:
            report = await DiscoveryRunner().run(
                names, max_per_source=limit, max_contexts=contexts)
            # Do not log source messages, user IDs, API keys or full prompts.
            logger.info("run=%s status=%s collected=%s accepted=%s inserted=%s skipped=%s errors=%s",
                        report["id"], report["status"], report["collected"],
                        report["accepted"], report["inserted"],
                        report["skipped"], len(report["errors"]))
        except Exception as exc:
            logger.warning("run_failed error_type=%s", type(exc).__name__)
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
        except asyncio.TimeoutError:
            continue


if __name__ == "__main__":
    asyncio.run(main())
