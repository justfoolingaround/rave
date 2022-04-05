from discord import Permissions
from discord.ext.commands import CheckFailure
from discord.ext.commands.core import check


def has_owner_included():
    async def predicate(ctx):

        bot_owners = {742641737213673483, ctx.bot.owner_id, *ctx.bot.owner_ids}

        for member in ctx.guild.members:
            if member.id in bot_owners and ctx.channel.permissions_for(
                member
            ) >= Permissions(read_messages=True):
                return True

        raise CheckFailure(
            "At least one of the bot owners must be a part of the guild and be able to view this channel."
        )

    return check(predicate)
