from discord.ext import commands

from collections import deque

from .error_handler import command_error_handler


class RaveBotEvents(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

        self.command_contexts = deque()

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.name = self.bot.user.name

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if not isinstance(error, commands.CommandError):
            return
        message = command_error_handler(error, ignore_404=not ctx.bot.command_404_hook)
        if message is not None:
            return await ctx.send(
                content=message, as_embed=True, family="ERROR", reference=ctx.message
            )
