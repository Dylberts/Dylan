from redbot.core import commands
import discord

intents = discord.Intents.default()
intents.members = True  # Ensure the bot can see member roles

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

class RoleReplace(commands.Cog, name="RoleReplace"):
    def __init__(self, bot):
        self.bot = bot
        self.role_ids = {
            1235573502459904042,  # Role gold
            1235798008126246983,  # Role silver
            1235798803425132624,  # Role bronze
            1233254368963334185,  # Role 1
            1233254790406869005,  # Role 2
            1233255218817404938,  # Role 3
            1233256062946246666,  # Role 4
            1233256207112732812,  # Role 5
            1233256301660864554,  # Role 6
            1233256478228484116,  # Role 7
            1233256570247188510   # Role 8
        }

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        print(f"RoleReplace: Member update detected for {after.name}")
        new_roles = set(after.roles) - set(before.roles)
        new_role_ids = {role.id for role in new_roles}

        print(f"Roles before update: {[role.id for role in before.roles]}")
        print(f"Roles after update: {[role.id for role in after.roles]}")
        print(f"New roles detected: {new_role_ids}")

        for role_id in new_role_ids:
            if role_id in self.role_ids:
                print(f"New role {role_id} is in the managed role list.")
                roles_to_remove = [old_role for old_role in before.roles if old_role.id in self.role_ids and old_role.id != role_id]
                if roles_to_remove:
                    await after.remove_roles(*roles_to_remove)
                    for old_role in roles_to_remove:
                        print(f"Removed role {old_role.id} from {after.name}")
                break

async def setup(bot):
    bot.add_cog(RoleLock(bot))
    bot.add_cog(RoleReplace(bot))
