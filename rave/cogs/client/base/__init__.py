from .cog import RaveBotBase


def setup(bot):
    bot.add_cog(RaveBotBase(bot))
