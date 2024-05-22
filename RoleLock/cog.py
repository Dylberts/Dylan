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
            1235573502459904042: [1235798008126246983, 1235798803425132624],
            1235798008126246983: [1235573502459904042, 1235798803425132624],
            1235798803425132624: [1235573502459904042, 1235798008126246983],
            1233254368963334185: [1233254790406869005, 1233255218817404938, 1233256062946246666, 1233256207112732812, 1233256301660864554, 1233256478228484116, 1233256570247188510],
            1233254790406869005: [1233254368963334185, 1233255218817404938, 1233256062946246666, 1233256207112732812, 1233256301660864554, 1233256478228484116, 1233256570247188510],
            1233255218817404938: [1233254368963334185, 1233254790406869005, 1233256062946246666, 1233256207112732812, 1233256301660864554, 1233256478228484116, 1233256570247188510],
            1233256062946246666: [1233254368963334185, 1233254790406869005, 1233255218817404938, 1233256207112732812, 1233256301660864554, 1233256478228484116, 1233256570247188510],
            1233256207112732812: [1233254368963334185, 1233254790406869005, 1233255218817404938, 1233256062946246666, 1233256301660864554, 1233256478228484116, 1233256570247188510],
            1233256301660864554: [1233254368963334185, 1233254790406869005, 1233255218817404938, 1233256062946246666, 1233256207112732812, 1233256478228484116, 1233256570247188510],
            1233256478228484116: [1233254368963334185, 1233254790406869005, 1233255218817404938, 1233256062946246666, 1233256207112732812, 1233256301660864554, 1233256570247188510],
            1233256570247188510: [1233254368963334185, 1233254790406869005, 1233255218817404938, 1233256062946246666, 1233256207112732812, 1233256301660864554, 1233256478228484116],
        }

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        await self.check_and_update_roles(before, after)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            if member:
                await self.check_and_update_roles(member)

    async def check_and_update_roles(self, before, after=None):
        if after is None:
            after = before

        before_roles = {role.id for role in before.roles}
        after_roles = {role.id for role in after.roles}

        for locked_role_id, blocked_role_ids in self.locked_roles.items():
            if locked_role_id in before_roles and locked_role_id not in after_roles:
                for role_id in blocked_role_ids:
                    if role_id in after_roles:
                        locked_role = discord.utils.get(after.guild.roles, id=locked_role_id)
                        new_role = discord.utils.get(after.guild.roles, id=role_id)
                        if locked_role and new_role:
                            await after.remove_roles(locked_role)
                            await after.add_roles(new_role)
                            print(f"Replaced {locked_role.name} with {new_role.name} for {after.display_name}")
                            break
                        
def setup(bot):
    bot.add_cog(RoleLock(bot))
    bot.add_cog(RoleReplace(bot))
