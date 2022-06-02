import asyncio
from enum import Enum


class UserType(Enum):

    FEIGN = 0
    SNEAK = 1
    TRUTH = 2


class SneakyHandler:
    def __init__(self, bot, guild, *, real_online_count):

        self.bot = bot
        self.guild = guild

        self.sneakies = set()

        self.real_online_count = real_online_count
        self.user_lock = asyncio.Lock()

    @property
    def online_members(self):
        return [
            member for member in self.guild.members if member.raw_status != "offline"
        ]

    @property
    def online_members_count(self):
        return len(self.online_members)

    @staticmethod
    async def get_real_online_count(bot, guild_id) -> int:
        return (await bot.http.get_widget(guild_id))["presence_count"]

    async def determine_by_presence_change(self, before_presence):

        async with self.user_lock:

            if before_presence == "offline":
                expected_count = self.real_online_count + 1
                real_count = await self.get_real_online_count(self.bot, self.guild.id)

                if real_count == expected_count:
                    determinant = UserType.TRUTH
                else:
                    determinant = UserType.FEIGN
            else:
                expected_count = self.real_online_count - 1
                real_count = await self.get_real_online_count(self.bot, self.guild.id)

                if real_count == expected_count:
                    determinant = UserType.TRUTH
                else:
                    determinant = UserType.SNEAK

            self.real_online_count = real_count

        return determinant
