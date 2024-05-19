from redbot.core import commands
import discord

class RoleLock(commands.Cog, name="RoleLock"):
    def __init__(self, bot):
        self.bot = bot
        self.locked_role_id = 1233366060477186048 '''@Age (13-17) Role ID''' # Replace with the ID of the role you want to lock
        self.blocked_role_id = 1233366502451712074, 1233366641572712520, 1233366931302776843 '''@Age (18-25), @Age (26-35), @Age (36-48+) Role ID''' # Replace with the ID of the role you want to block 

    @commands.Cog.listener(name="RoleLock")
    async def on_member_update(self, before, after):
        if self.locked_role_id in [role.id for role in after.roles]:
            if self.blocked_role_id in [role.id for role in after.roles]:
                await after.remove_roles(discord.Object(id=self.blocked_role_id))
                #await after.send("You cannot obtain this role while having the locked role.")

def setup(bot):
    bot.add_cog(RoleLock(bot))
