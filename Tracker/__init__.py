from .cog import Tracker


async def setup(bot):
    await bot.add_cog(Tracker(bot))
