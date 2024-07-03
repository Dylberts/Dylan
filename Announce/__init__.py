from .cog import Post


async def setup(bot):
    await bot.add_cog(Post(bot))
