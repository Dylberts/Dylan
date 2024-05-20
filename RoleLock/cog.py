from redbot.core import commands
import discord

##class RoleLock(commands.Cog, name="RoleLock"):
    ##def __init__(self, bot):
        ##self.bot = bot
        ##self.locked_role_id = 1233366060477186048  # @Age (13-17) Role ID > Replace with the ID of the role you want to lock
        ##self.blocked_role_ids = [1233366502451712074, 1233366641572712520, 1233366931302776843, 1233369491447091251]  # @Age (18-25), @Age (26-35), @Age (36-48+), @NSFW Role ID > Replace with the ID of the role you want to block 

    ##@commands.Cog.listener()
    ##async def on_member_update(self, before, after):
        ##for role in after.roles:
            ##if role.id in self.blocked_role_ids and self.locked_role_id in [role.id for role in after.roles]:
                ##await after.remove_roles(role)
                #await after.send("You cannot obtain this role while having the locked 
class RoleLock(commands.Cog, name="RoleLock"):
    def __init__(self, bot):
        self.bot = bot
        self.locked_roles = {
            # @Age (13-17): [Blocked Roles: @Age (18-25), @Age (26-35), @Age (26-35), @Age (36-48+), @NSFW]
            1233366060477186048: [1233366502451712074, 1233366641572712520, 1233366931302776843, 1233369491447091251],
            # @Guild Leader: [Blocked Roles: @Guild Deputy), @Guild Elite]
            1235573502459904042: [1235798008126246983, 1235798803425132624],
            # @Guild Deputy: [Blocked Roles: @Guild Leader), @Guild Elite]
            1235798008126246983: [1235573502459904042, 1235798803425132624],
            # @Guild Elite: [Blocked Roles: @Guild Leader), @Guild Deputy]
            1235798803425132624: [1235573502459904042, 1235798008126246983],
            # NOTE: You can add more entries for additional lock roles and their corresponding blocked roles
            # TODO: Simplify nest dictionary so it's not a massive list
        }

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        for locked_role_id, blocked_role_ids in self.locked_roles.items():
            if locked_role_id in [role.id for role in after.roles]:
                for role in after.roles:
                    if role.id in blocked_role_ids:
                        await after.remove_roles(role)
                        embed = discord.Embed(title="Role Blocked", description=f"This is a Test", color=discord.Color.red())
                        await after.send(embed=embed, delete_after=10)
                        #await after.send("") 
def setup(bot):
   bot.add_cog(RoleLock(bot))
