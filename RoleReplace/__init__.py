from .cog import RoleReplace


async def setup(bot):
    await bot.add_cog(RoleReplace(bot))
