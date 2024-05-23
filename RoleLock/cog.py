from redbot.core import commands
import discord

class RoleLock(commands.Cog, name="RoleLock"):
    def __init__(self, bot):
        self.bot = bot
        self.locked_roles = {
            # @Age (13-17): [Blocked Roles: @Age (18-25), @Age (26-35), @Age (36-48+), @NSFW]
            1233366060477186048: [1233366502451712074, 1233366641572712520, 1233366931302776843],
        }

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        print(f"RoleLock: Member update detected for {after.name}")
        for locked_role_id, blocked_role_ids in self.locked_roles.items():
            if locked_role_id in [role.id for role in after.roles]:
                for role in after.roles:
                    if role.id in blocked_role_ids:
                        await after.remove_roles(role)
                        print(f"RoleLock: Removed blocked role {role.id} from {after.name}")

async def setup(bot):
    bot.add_cog(RoleLock(bot))
