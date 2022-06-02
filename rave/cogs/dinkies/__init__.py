from .sneakies import SneakyCatcher


def setup(bot):
    bot.add_cog(
        SneakyCatcher(
            bot, guild_id=925000668824080474, disposal_channel=981821178710728814
        )
    )
