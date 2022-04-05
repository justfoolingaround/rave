from .cog import RaveBotEvents


def setup(bot):
    bot.add_cog(RaveBotEvents(bot))
