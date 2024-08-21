from .cog import ThreadBumper

def setup(bot: Red):
    bot.add_cog(ThreadBumper(bot))
