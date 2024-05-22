from redbot.core import commands, Config
import discord
from redbot.core.bot import Red
import logging

log = logging.getLogger("red.RoleReplace")

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

class RoleReplace(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Replace with a unique identifier
        default_guild = {
            "role_to_watch": None,
            "roles_to_replace": []
        }
        self.config.register_guild(**default_guild)

    @commands.group()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def rolereplace(self, ctx):
        """Manage RoleReplace settings."""
        pass

    @rolereplace.command()
    async def setrole(self, ctx, role: discord.Role):
        """Set the role to watch for."""
        await self.config.guild(ctx.guild).role_to_watch.set(role.id)
        await ctx.send(f"Role to watch set to: {role.name}")

    @rolereplace.command()
    async def addrole(self, ctx, role: discord.Role):
        """Add a role to the list of roles to replace."""
        async with self.config.guild(ctx.guild).roles_to_replace() as roles:
            if role.id not in roles:
                roles.append(role.id)
                await ctx.send(f"Role {role.name} added to the replacement list.")
            else:
                await ctx.send(f"Role {role.name} is already in the replacement list.")

    @rolereplace.command()
    async def removerole(self, ctx, role: discord.Role):
        """Remove a role from the list of roles to replace."""
        async with self.config.guild(ctx.guild).roles_to_replace() as roles:
            if role.id in roles:
                roles.remove(role.id)
                await ctx.send(f"Role {role.name} removed from the replacement list.")
            else:
                await ctx.send(f"Role {role.name} is not in the replacement list.")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        guild = after.guild
        role_to_watch_id = await self.config.guild(guild).role_to_watch()
        roles_to_replace = await self.config.guild(guild).roles_to_replace()

        if role_to_watch_id is None or not roles_to_replace:
            return

        role_to_watch = guild.get_role(role_to_watch_id)
        if role_to_watch in after.roles and role_to_watch not in before.roles:
            # User has gained the watched role
            roles_to_remove = [guild.get_role(role_id) for role_id in roles_to_replace if guild.get_role(role_id) in after.roles]
            if roles_to_remove:
                await after.remove_roles(*roles_to_remove, reason="RoleReplace: Replacing old roles with the new role")
                await after.add_roles(role_to_watch, reason="RoleReplace: Adding the new role")
                self.log_role_change(after, role_to_watch, roles_to_remove)

    def log_role_change(self, member: discord.Member, new_role: discord.Role, removed_roles: list):
        """Log the role changes in the console."""
        removed_roles_names = [role.name for role in removed_roles]
        removed_roles_str = ", ".join(removed_roles_names)
        log.info(f"Member {member} had roles {removed_roles_str} replaced with {new_role.name}")

async def setup(bot):
    bot.add_cog(RoleLock(bot))
    bot.add_cog(RoleReplace(bot))
