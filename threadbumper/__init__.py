from .cog import threadbumper


async def setup(bot):
    await bot.add_cog(threadbumper(bot))
