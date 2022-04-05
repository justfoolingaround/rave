import random

import discord
import httpx
from discord.ext import commands

from .cleverbot import SERVICES, CleverBotClient
from .utils import Ratelimit

RAW_CHANNEL = ("rave", "rave-waiifu", "rave-the-waiifu")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36",
}


def iter_channel_names(channels, *, from_names):
    for channel in channels:
        if channel.name.lower() in from_names:
            yield channel


class CleverBotCog(commands.Cog):

    allowed_mentions = discord.AllowedMentions(users=False, roles=False, everyone=False)

    def __init__(self, bot):
        self.bot: commands.Bot = bot

        self.clients: dict[int, CleverBotClient] = {}

        self.user_ratelimit = Ratelimit(exemptions=[742641737213673483])

    async def get_client(self, component_id: int):
        if component_id in self.clients:
            return self.clients[component_id]

        _, (url, service_endpoint) = random.choice(list(SERVICES.items()))

        client = await CleverBotClient.ainitialise(
            httpx.AsyncClient(headers=headers),
            url=url,
            service_endpoint=service_endpoint,
        )

        self.clients.update({component_id: client})
        return client

    @commands.command("cb")
    async def cleverbotto(self, ctx, *, query):
        is_ratelimited, _ = await self.user_ratelimit.perform(ctx.author.id)

        if is_ratelimited:
            return await ctx.send(
                "{}-san~, you're being ratelimited, please try again~".format(
                    ctx.author.display_name
                ),
                reference=ctx.message,
                allowed_mentions=self.allowed_mentions,
            )

        client = await self.get_client(ctx.message.author.id)
        response = await client.acommunicate(query)

        if response is not None:
            return await ctx.message.channel.send(
                response, reference=ctx.message, allowed_mentions=self.allowed_mentions
            )

    @commands.Cog.listener("on_message")
    async def on_channels_message(self, message: discord.Message):

        if (
            not message.guild
            or message.author.id == self.bot.user.id
            or message.channel.id
            not in list(
                map(
                    lambda channel: channel.id,
                    iter_channel_names(message.guild.channels, from_names=RAW_CHANNEL),
                )
            )
        ):
            return

        is_ratelimited, _ = await self.user_ratelimit.perform(message.author.id)

        if is_ratelimited:
            return await message.channel.send(
                "{}-san~, you're being ratelimited, please try again~".format(
                    message.author.display_name
                ),
                reference=message,
                allowed_mentions=self.allowed_mentions,
            )

        client = await self.get_client(message.author.id)
        response = await client.acommunicate(message.content)

        if response is not None:
            return await message.channel.send(
                response, reference=message, allowed_mentions=self.allowed_mentions
            )


def setup(bot):
    bot.add_cog(CleverBotCog(bot))
