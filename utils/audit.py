import os
import logging
import aiohttp
import discord

LOGGER = logging.getLogger(__name__)

AUDIT_WEBHOOK_URL = os.getenv("AUDIT_WEBHOOK_URL")


async def send_audit_log(message: str) -> None:
    if not AUDIT_WEBHOOK_URL:
        return

    try:
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(AUDIT_WEBHOOK_URL, session=session)
            await webhook.send(message)
    except Exception:
        LOGGER.exception("Audit log send failed")



