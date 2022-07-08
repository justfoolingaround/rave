import re
from datetime import datetime

import discord
import httpx
from discord.ext import commands, tasks
from humanize import naturaldelta

STAR_VC_ENDPOINT = "https://canary.discord.com/api/v9/channels/925026111648321586"
STAR_GITHUB_REPO = "justfoolingaround/animdl"
STAR_REGEX = re.compile(r'aria-label="(\d+) users starred this repository"')


class RaveBotBase(commands.Cog):

    star_count = None

    def __init__(self, bot):
        self.bot = bot
        self.initialization = datetime.now()

        self.http_client = httpx.AsyncClient(follow_redirects=True)

        self.star_task = self.discord_channel_stars.start()

    @tasks.loop(minutes=5)
    async def discord_channel_stars(self):
        """
        Update the amount of stars in the vc name.

        Not using GitHub API because it's ratelimited.
        """
        new_star_count = int(
            STAR_REGEX.search(
                (
                    await self.http_client.get(f"https://github.com/{STAR_GITHUB_REPO}")
                ).text
            ).group(1)
        )

        if self.star_count is not None and new_star_count == self.star_count:
            return

        self.star_count = new_star_count

        return await self.http_client.patch(
            STAR_VC_ENDPOINT,
            json={
                "name": f"🌟 {new_star_count}",
                "topic": "The greatest vc of all time!",
            },
            headers={"Authorization": f"Bot {self.bot.http.token}"},
        )

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
