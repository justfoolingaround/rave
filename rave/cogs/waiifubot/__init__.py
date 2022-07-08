import contextvars
import functools
from asyncio import get_running_loop
from collections import defaultdict

import discord
from discord.ext import commands

from .cleverbot import get_unique_client


async def to_thread(func, *args, **kwargs):

    loop = get_running_loop()
    ctx = contextvars.copy_context()
    func_call = functools.partial(ctx.run, func, *args, **kwargs)
    return await loop.run_in_executor(None, func_call)


RAW_CHANNEL = ("rave", "rave-waiifu", "rave-the-waiifu")


def iter_channel_names(channels, *, from_names):
    for channel in channels:
        if channel.name.lower() in from_names:
            yield channel


class CleverBotCog(commands.Cog):

    allowed_mentions = discord.AllowedMentions(users=False, roles=False, everyone=False)

    def __init__(self, bot):
        self.bot: commands.Bot = bot

        self.sent_messages = defaultdict(set)

        self.clever_bot_services = defaultdict(get_unique_client)

    @commands.command("cb")
    async def cleverbot_call(self, ctx, *, query):

        ctx.message.content = query

        return await self.on_channels_message(ctx.message, sudo=True)

    @commands.Cog.listener("on_message")
    async def on_channels_message(self, message: discord.Message, *, sudo=False):

        if not sudo and (
            not message.guild
            or message.author.bot
            or message.channel.id
            not in list(
                map(
                    lambda channel: channel.id,
                    iter_channel_names(message.guild.channels, from_names=RAW_CHANNEL),
                )
            )
            and (
                message.reference
                and message.reference.message_id
                not in self.sent_messages[message.author.id]
            )
        ):
            return

        webservice = self.clever_bot_services[message.author.id]

        response = await to_thread(webservice.talk, message.content)

        sent_message = await message.channel.send(
            response, reference=message, allowed_mentions=self.allowed_mentions
        )
        self.sent_messages[message.author.id].add(sent_message.id)


def setup(bot):
    bot.add_cog(CleverBotCog(bot))
