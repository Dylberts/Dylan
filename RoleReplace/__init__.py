from .cog import RoleReplace

cog = bot.get_cog("RoleTools")
if cog:
    print("RoleTools cog is loaded.")
else:
    print("RoleTools cog is not loaded.")
    
async def setup(bot):
    await bot.add_cog(RoleReplace(bot))
