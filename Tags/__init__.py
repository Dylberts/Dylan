from .cog import Tags


async def setup(bot):
    await bot.add_cog(Tags(bot))
