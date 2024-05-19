from .cog import RoleLock


async def setup(bot):
    await bot.add_cog(RoleLock(bot))
