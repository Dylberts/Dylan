from .cog import ThreadBumper


async def setup(bot):
    await bot.add_cog(ThreadBumper(bot))
