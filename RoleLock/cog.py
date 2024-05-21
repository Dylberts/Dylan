from redbot.core import commands
import discord

class RoleLock(commands.Cog, name="RoleLock"):
    def __init__(self, bot):
        self.bot = bot
        self.locked_roles = {
            # @Age (13-17): [Blocked Roles: @Age (18-25), @Age (26-35), @Age (26-35), @Age (36-48+), @NSFW]
            1233366060477186048: [1233366502451712074, 1233366641572712520, 1233366931302776843],
            # All role ID's nested are in the order listed
        }

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        for locked_role_id, blocked_role_ids in self.locked_roles.items():
            if locked_role_id in [role.id for role in after.roles]:
                for role in after.roles:
                    if role.id in blocked_role_ids:
                        await after.remove_roles(role)

 class RoleReplace(commands.Cog, name="RoleReplace"):
     def __init__(self, bot):
         self.bot = bot
         self.locked_roles = {
             # @Age (13-17): [Blocked Roles: @Age (18-25), @Age (26-35), @Age (36-48+), @NSFW]
             1233366060477186048: [1233366502451712074, 1233366641572712520, 1233366931302776843, 1233369491447091251],
             # @Guild Leader: [Blocked Roles: @Guild Deputy, @Guild Elite]
             1235573502459904042: [1235798008126246983, 1235798803425132624],
             # @Guild Deputy: [Blocked Roles: @Guild Leader, @Guild Elite]
             1235798008126246983: [1235573502459904042, 1235798803425132624],
             # @Guild Elite: [Blocked Roles: @Guild Leader, @Guild Deputy]
             1235798803425132624: [1235573502459904042, 1235798008126246983],
             # @S-201: [Blocked Roles: @S-202, @S-203, @S-204, @S-205, @S-206, @S-207, @S-208]
             1233254368963334185: [1233254790406869005, 1233255218817404938, 1233256062946246666, 1233256207112732812, 1233256301660864554, 1233256478228484116, 1233256570247188510],
             # @S-202: [Blocked Roles: @S-201, @S-203, @S-204, @S-205, @S-206, @S-207, @S-208]
             1233254790406869005: [1233254368963334185, 1233255218817404938, 1233256062946246666, 1233256207112732812, 1233256301660864554, 1233256478228484116, 1233256570247188510],
             # @S-203: [Blocked Roles: @S-201, @S-202, @S-204, @S-205, @S-206, @S-207, @S-208]
             1233255218817404938: [1233254368963334185, 1233254790406869005, 1233256062946246666, 1233256207112732812, 1233256301660864554, 1233256478228484116, 1233256570247188510],
             # @S-204: [Blocked Roles: @S-201, @S-202, @S-203, @S-205, @S-206, @S-207, @S-208]
             1233256062946246666: [1233254368963334185, 1233254790406869005, 1233255218817404938, 1233256207112732812, 1233256301660864554, 1233256478228484116, 1233256570247188510],
             # @S-205: [Blocked Roles: @S-201, @S-202, @S-203, @S-204, @S-206, @S-207, @S-208]
             1233256207112732812: [1233254368963334185, 1233254790406869005, 1233255218817404938, 1233256062946246666, 1233256301660864554, 1233256478228484116, 1233256570247188510],
             # @S-206: [Blocked Roles: @S-201, @S-202, @S-203, @S-204, @S-205, @S-207, @S-208]
             1233256301660864554: [1233254368963334185, 1233254790406869005, 1233255218817404938, 1233256062946246666, 1233256207112732812, 1233256478228484116, 1233256570247188510],
             # @S-207: [Blocked Roles: @S-201, @S-202, @S-203, @S-204, @S-205, @S-206, @S-208]
             1233256478228484116: [1233254368963334185, 1233254790406869005, 1233255218817404938, 1233256062946246666, 1233256207112732812, 1233256301660864554, 1233256570247188510],
             # @S-208: [Blocked Roles: @S-201, @S-202, @S-203, @S-204, @S-205, @S-206, @S-207]
             1233256570247188510: [1233254368963334185, 1233254790406869005, 1233255218817404938, 1233256062946246666, 1233256207112732812, 1233256301660864554, 1233256478228484116],
             # All roles ID's nested are in the order provided
        }

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        for locked_role_id, blocked_role_ids in self.locked_roles.items():
            # Check if the member has a locked role
            if locked_role_id in [role.id for role in before.roles]:
                for role in after.roles:
                    # If the member gets a blocked role, replace the locked role
                    if role.id in blocked_role_ids:
                        locked_role = discord.utils.get(after.guild.roles, id=locked_role_id)
                        if locked_role:
                            await after.remove_roles(locked_role)
                        await after.add_roles(role)
                        break
                    
def setup(bot):
    bot.add_cog(RoleLock(bot))
    bot.add_cog(RoleReplace(bot))
