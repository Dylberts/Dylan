from .cog import MadLib


async def setup(bot):
    await bot.add_cog(MadLib(bot))
