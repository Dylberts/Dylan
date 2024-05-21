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
        self.role_replacements = {
            # @New Role: @Old Role to replace
            1235573502459904042: 1235798008126246983,  # @Guild Leader replaces @Guild Deputy
            1235798008126246983: 1235798803425132624,  # @Guild Deputy replaces @Guild Elite
            1235798803425132624: 1235573502459904042,  # @Guild Elite replaces @Guild Leader
            1233254368963334185: 1233254790406869005,  # @S-201 replaces @S-202
            1233254790406869005: 1233255218817404938,  # @S-202 replaces @S-203
            1233255218817404938: 1233256062946246666,  # @S-203 replaces @S-204
            1233256062946246666: 1233256207112732812,  # @S-204 replaces @S-205
            1233256207112732812: 1233256301660864554,  # @S-205 replaces @S-206
            1233256301660864554: 1233256478228484116,  # @S-206 replaces @S-207
            1233256478228484116: 1233256570247188510,  # @S-207 replaces @S-208
            1233256570247188510: 1233254368963334185,  # @S-208 replaces @S-201
        }
        
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        before_role_ids = {role.id for role in before.roles}
        after_role_ids = {role.id for role in after.roles}

        # Detect newly added roles
        newly_added_roles = after_role_ids - before_role_ids

        for new_role_id in newly_added_roles:
            if new_role_id in self.role_replacements:
                old_role_id = self.role_replacements[new_role_id]
                old_role = discord.utils.get(after.guild.roles, id=old_role_id)
                new_role = discord.utils.get(after.guild.roles, id=new_role_id)

                if old_role in after.roles:
                    await after.remove_roles(old_role)
                    await after.add_roles(new_role)

def setup(bot):
    bot.add_cog(RoleLock(bot))
    bot.add_cog(RoleReplace(bot))
