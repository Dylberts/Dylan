from .cog import Quote


async def setup(bot):
    await bot.add_cog(Quote(bot))
