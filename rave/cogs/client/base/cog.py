from datetime import datetime

import discord
from discord.ext import commands
from humanize import naturaldelta


class RaveBotBase(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.initialization = datetime.now()

    @commands.group(invoke_without_command=True)
    async def rave(self, ctx):
        return await ctx.send(
            "\n\n".join(
                [
                    "Rave, an open-sourced bot.",
                    "Client latency: `{:.2f}ms`, bot loaded {} ago.".format(
                        ctx.bot.latency * 1000, naturaldelta(self.initialization)
                    ),
                    "**{}** active extensions (inclusive): \n- {}".format(
                        len(ctx.bot.extensions), ",\n- ".join(ctx.bot.extensions)
                    ),
                    "Using discord.py v{.__version__} & Rave v{.__version__}.".format(
                        discord, ctx.bot
                    ),
                ]
            ),
            as_embed=True,
        )
