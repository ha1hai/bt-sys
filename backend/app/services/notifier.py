import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def notify(bot, message: str) -> None:
    text = f"[{bot.name}] {message}"
    await _discord(text)
    await _line(text)


async def _discord(text: str) -> None:
    if not settings.discord_webhook_url:
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(settings.discord_webhook_url, json={"content": text}, timeout=5)
    except Exception as e:
        logger.warning(f"Discord notify failed: {e}")


async def _line(text: str) -> None:
    if not settings.line_channel_access_token:
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://api.line.me/v2/bot/message/broadcast",
                headers={"Authorization": f"Bearer {settings.line_channel_access_token}"},
                json={"messages": [{"type": "text", "text": text}]},
                timeout=5,
            )
    except Exception as e:
        logger.warning(f"LINE notify failed: {e}")
