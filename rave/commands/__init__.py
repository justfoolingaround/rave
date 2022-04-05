from discord.abc import Messageable
from discord.embeds import Embed
from discord.ext.commands import Bot, Context, Cog
import discord

from jishaku.paginators import (
    PaginatorEmbedInterface,
    PaginatorInterface,
    WrappedPaginator,
)


def smart_separation(string: str, max_length, separators=[" ", "\n"]):
    if not string:
        return

    if len(string) <= max_length:
        yield string
        return

    separator, separator_index = max(
        ((_, string[:max_length].rfind(_)) for _ in separators), key=lambda x: x[1]
    )

    if separator_index == -1:
        separator, separator_index = "", max_length

    yield string[:separator_index]
    yield from smart_separation(
        string[separator_index + len(separator) :], max_length, separators=separators
    )


class AdjustibleMessageable(Messageable):

    families = {
        "INFO": 0x41B883,
        "DEBUG": 0x3572A5,
        "WARNING": 0xF1E05A,
        "CRITICAL": 0xA21A1E,
        "ERROR": 0xC03723,
    }

    async def send(
        self, content=None, *, embed=None, as_embed=False, family="DEBUG", **kwargs
    ):
        if embed and as_embed:
            raise Exception(
                "embed cannot be set if the message content was set to be sent as an embed itself."
            )

        limit = 4000

        sent = []

        if content:
            for separated in smart_separation(content, max_length=limit):
                if as_embed:
                    sent.append(
                        await super().send(
                            embed=Embed(
                                description=separated,
                                color=self.families.get(family.upper(), 0x3572A5),
                            ),
                            **kwargs
                        )
                    )
                else:
                    sent.append(await super().send(separated, embed=embed, **kwargs))

            return sent[-1]

        message = await super().send(content=content, embed=embed, **kwargs)
        return message


class AdjustibleCog(Cog):
    @staticmethod
    async def send_viewer(ctx, content, *, color=None, title=None, **embed_kwargs):
        paginator = WrappedPaginator(prefix="", suffix="", max_size=2000)
        embed_permissions = ctx.channel.permissions_for(ctx.guild.me).is_superset(
            discord.Permissions(1 << 14)
        )

        kwargs = {
            "owner": ctx.author,
            "bot": ctx.bot,
            "paginator": paginator,
        }

        if embed_permissions:
            cls = PaginatorEmbedInterface

            embed = discord.Embed.from_dict(
                {
                    "footer": {
                        "text": "For you, {}".format(ctx.author),
                        "icon_url": str(ctx.author.avatar_url),
                    },
                    **embed_kwargs,
                }
            )

            if title is not None:
                embed.title = title

            embed.color = color or discord.Colour.purple()
            kwargs.update({"embed": embed})

        else:
            cls = PaginatorInterface

        inteface = cls(**kwargs)

        await inteface.add_line(content)
        return await inteface.send_to(ctx)

    @staticmethod
    async def send_smartly(
        ctx,
        message_content,
        *,
        footer="For you, {}",
        color=None,
        title=None,
        **embed_kwargs
    ):

        if len(message_content) > 2000:
            return await AdjustibleCog.send_viewer(
                ctx, message_content, title=title, color=color, **embed_kwargs
            )

        embed_permissions = ctx.channel.permissions_for(ctx.guild.me).is_superset(
            discord.Permissions(1 << 14)
        )

        kwargs = {"reference": ctx.message}

        if embed_permissions:
            embed = discord.Embed.from_dict(
                {
                    "description": message_content,
                    "footer": {
                        "text": footer.format(ctx.author),
                        "icon_url": str(ctx.author.avatar_url),
                    },
                    **embed_kwargs,
                }
            )

            if title is not None:
                embed.title = title

            embed.color = color or discord.Colour.random()
            kwargs.update({"embed": embed})
        else:
            kwargs.update({"content": message_content})

        return await ctx.send(**kwargs)


class AdjustibleContext(Context, AdjustibleMessageable):
    bot: Bot
