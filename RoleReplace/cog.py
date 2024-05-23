import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
import logging

log = logging.getLogger("red.RoleReplace")

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
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `setrole`, `addroles`, or `removeroles` subcommands to configure role replacement.")

    @rolereplace.command()
    async def setrole(self, ctx, role: discord.Role):
        """Set the role to watch for."""
        await self.config.guild(ctx.guild).role_to_watch.set(role.id)
        await ctx.send(f"Role to watch set to: {role.name}")

    @rolereplace.command()
    async def addroles(self, ctx, *roles: discord.Role):
        """Add roles to the list of roles to replace."""
        async with self.config.guild(ctx.guild).roles_to_replace() as roles_to_replace:
            added_roles = []
            for role in roles:
                if role.id not in roles_to_replace:
                    roles_to_replace.append(role.id)
                    added_roles.append(role.name)
            if added_roles:
                await ctx.send(f"Roles {', '.join(added_roles)} added to the replacement list.")
            else:
                await ctx.send("No new roles were added to the replacement list.")

    @rolereplace.command()
    async def removeroles(self, ctx, *roles: discord.Role):
        """Remove roles from the list of roles to replace."""
        async with self.config.guild(ctx.guild).roles_to_replace() as roles_to_replace:
            removed_roles = []
            for role in roles:
                if role.id in roles_to_replace:
                    roles_to_replace.remove(role.id)
                    removed_roles.append(role.name)
            if removed_roles:
                await ctx.send(f"Roles {', '.join(removed_roles)} removed from the replacement list.")
            else:
                await ctx.send("No roles were removed from the replacement list.")

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

def setup(bot: Red):
    bot.add_cog(RoleReplace(bot))
