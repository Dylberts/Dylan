from .cog import QuoteCog


async def setup(bot):
    await bot.add_cog(QuoteCog(bot))
