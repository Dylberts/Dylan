from .cog import Guest


async def setup(bot):
    await bot.add_cog(Guest(bot))
