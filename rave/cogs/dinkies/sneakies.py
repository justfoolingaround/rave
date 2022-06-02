import io

import disnake
from disnake.ext import commands
from disnake.http import Route

from .utils import SneakyHandler, UserType


class SneakyCatcher(commands.Cog):
    def __init__(self, bot, *, guild_id=None, disposal_channel: int):
        self.bot: commands.Bot = bot

        self.guild_id = guild_id
        self.disposal_channel = disposal_channel

        self.sneaky_handler = None

    @commands.Cog.listener()
    async def on_ready(self):

        guild = self.bot.get_guild(self.guild_id)

        if guild is None:
            return

        try:
            presence_count = await SneakyHandler.get_real_online_count(
                self.bot, self.guild_id
            )
        except disnake.Forbidden:
            return

        self.sneaky_handler = SneakyHandler(
            self.bot, guild, real_online_count=presence_count
        )

    async def announce(self, message):
        return await self.bot.http.request(
            Route(
                "POST",
                f"/channels/{self.disposal_channel}/messages",
            ),
            json={"content": message},
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):

        if self.sneaky_handler is None or member.guild_id != self.guild_id:
            return

        if member.raw_status == "offline":
            await self.announce(
                f"Sneaky **{member}** `{member.id}`: joins while offline."
            )

        async with self.sneaky_handler.user_lock:
            self.sneaky_handler.real_online_count += 1

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member):

        if self.sneaky_handler is None or member.guild.id != self.guild_id:
            return

        if member.raw_status == "offline":
            await self.announce(f"**{member}** `{member.id}`: leaves while offline.")

        if member.id in self.sneaky_handler.sneakies:
            self.sneaky_handler.sneakies.remove(member.id)

        async with self.sneaky_handler.user_lock:
            self.sneaky_handler.real_online_count -= 1

    @commands.Cog.listener()
    async def on_presence_update(self, before: disnake.Member, after: disnake.Member):

        if self.sneaky_handler is None or before.guild.id != self.guild_id:
            return

        is_online = lambda member: member.raw_status != "offline"

        if (
            is_online(before)
            and is_online(after)
            or not (is_online(before) or is_online(after))
        ):
            return

        sneaky_user_type = await self.sneaky_handler.determine_by_presence_change(
            before.raw_status
        )

        if sneaky_user_type == UserType.SNEAK:
            self.sneaky_handler.sneakies.add(after.id)

            await self.announce(
                f"**{after}** `{after.id}`: Went from {before.raw_status} to invisible."
            )
        else:
            if after.id in self.sneaky_handler.sneakies:
                self.sneaky_handler.sneakies.remove(after.id)

            if sneaky_user_type == UserType.FEIGN:
                await self.announce(
                    f"**{after}** `{after.id}`: Went from invisible to {after.raw_status}."
                )

    @commands.Cog.listener()
    async def on_typing(self, channel: disnake.TextChannel, user, when):

        if (
            self.sneaky_handler is None
            or channel.guild is None
            or channel.guild.id != self.guild_id
        ):
            return

        if user.raw_status == "offline":
            self.sneaky_handler.sneakies.add(user.id)
            return await self.announce(
                f"Sneaky **{user}** `{user.id}`: types while invisible."
            )

    @commands.command()
    async def sneaky(self, ctx):
        if self.sneaky_handler is None:
            return await ctx.send(
                "A guild sneaky handler is not set, ensure that the guild exists and has widgets enabled."
            )

        count = (
            self.sneaky_handler.real_online_count
            - self.sneaky_handler.online_members_count
        )
        sneaky_count = len(self.sneaky_handler.sneakies)

        return await ctx.send(
            f"As of right now, there are **{count}** users in the guild who are invisible, {sneaky_count} of which are identified, this means every offline user has a {(count - sneaky_count) / len(self.sneaky_handler.guild.members) * 100:.2f}% chance of being a sneaky one."
        )

    @commands.command()
    async def sneakies(self, ctx):
        if self.sneaky_handler is None:
            return await ctx.send(
                "A guild sneaky handler is not set, ensure that the guild exists and has widgets enabled."
            )

        if not self.sneaky_handler.sneakies:
            return await ctx.send(
                "No sneakies found as of right now, still watching, don't you worry."
            )

        sneakies_io = io.BytesIO(
            "\n".join(map(str, self.sneaky_handler.sneakies)).encode("utf-8")
        )

        return await ctx.send(file=disnake.File(sneakies_io, filename="sneakies.txt"))
