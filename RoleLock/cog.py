from redbot.core import commands
import discord

class RoleLock(commands.Cog, name="RoleLock"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener(name="RoleLock")
    async def on_member_update(self, before, after):
        # Check if the specific role has been obtained
        specific_role = discord.utils.get(after.roles, name.id="1233366060477186048") # @Age (13-17)
        if specific_role:
            # Remove other roles specified
            roles_to_remove = ["1233366502451712074", "1233366641572712520", "1233366931302776843"] # @Age (18-25), (26-35), (36-48+)
            roles_to_remove = [discord.utils.get(after.guild.roles, name.id=role_name) for role_name in roles_to_remove]
            roles_to_remove = [role for role in roles_to_remove if role is not None]  # Filter out None values

            # If the user is attempting to obtain other roles, remove them
            if any(role in after.roles for role in roles_to_add):
                await after.remove_roles(*roles_to_add)

def setup(bot):
    bot.add_cog(RoleLock(bot))
