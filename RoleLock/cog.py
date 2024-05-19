from redbot.core import commands
import discord

class RoleLock(commands.Cog, name="RoleLock"):
    def __init__(self, bot):
        self.bot = bot
        self.locked_role_id = 1234567890  # Replace with the ID of the role you want to lock
        self.blocked_role_id = 0987654321  # Replace with the ID of the role you want to block

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if self.locked_role_id in [role.id for role in after.roles]:
            if self.blocked_role_id in [role.id for role in after.roles]:
                await after.remove_roles(discord.Object(id=self.blocked_role_id))
                await after.send("You cannot obtain this role while having the locked role.")

def setup(bot):
    bot.add_cog(RoleLock(bot))
