import httpx
from discord.ext import commands

from .commands import AdjustibleContext


class Color(object):
    error = 0xFF0000


class RaveBot(commands.Bot):
    """
    A cool discord bot.
    """

    __version__ = "1.0.0"

    color = Color()
    command_404_hook = False

    async def start(self, token, *, reconnect=True, session=None):
        """
        Override for .start async method for adding a core aiohttp session to the bot.
        """
        self.http_session = session or httpx.AsyncClient()
        return await super().start(token, reconnect=reconnect)

    async def close(self):
        """
        Override for .close async method for closing the aiohttp session of the bot.
        """
        return await self.http_session.aclose() and await super().close()

    async def process_commands(self, message):
        return await self.invoke(await self.get_context(message, cls=AdjustibleContext))
