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
            "role_sets": {}
        }
        self.config.register_guild(**default_guild)

    @commands.group()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def rolereplace(self, ctx):
        """Manage RoleReplace settings."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `addset`, `removeset`, `addwatchroles`, `removewatchroles`, `addroles`, `removeroles`, or `list` subcommands to configure role replacement.")

    @rolereplace.command()
    async def addset(self, ctx, set_name: str):
        """Add a new role set."""
        async with self.config.guild(ctx.guild).role_sets() as role_sets:
            if set_name in role_sets:
                await ctx.send(f"A role set with the name '{set_name}' already exists.")
            else:
                role_sets[set_name] = {"watch_roles": [], "replace_roles": []}
                await ctx.send(f"Role set '{set_name}' has been created.")

    @rolereplace.command()
    async def removeset(self, ctx, set_name: str):
        """Remove an existing role set."""
        async with self.config.guild(ctx.guild).role_sets() as role_sets:
            if set_name in role_sets:
                del role_sets[set_name]
                await ctx.send(f"Role set '{set_name}' has been removed.")
            else:
                await ctx.send(f"No role set with the name '{set_name}' exists.")

    @rolereplace.command()
    async def addwatchroles(self, ctx, set_name: str, *roles: discord.Role):
        """Add roles to watch for in a specific set."""
        async with self.config.guild(ctx.guild).role_sets() as role_sets:
            if set_name not in role_sets:
                await ctx.send(f"No role set with the name '{set_name}' exists.")
                return
            added_roles = []
            for role in roles:
                if role.id not in role_sets[set_name]["watch_roles"]:
                    role_sets[set_name]["watch_roles"].append(role.id)
                    added_roles.append(role.name)
            if added_roles:
                await ctx.send(f"Roles {', '.join(added_roles)} added to the watch list for set '{set_name}'.")
            else:
                await ctx.send("No new roles were added to the watch list.")

    @rolereplace.command()
    async def removewatchroles(self, ctx, set_name: str, *roles: discord.Role):
        """Remove roles from the watch list in a specific set."""
        async with self.config.guild(ctx.guild).role_sets() as role_sets:
            if set_name not in role_sets:
                await ctx.send(f"No role set with the name '{set_name}' exists.")
                return
            removed_roles = []
            for role in roles:
                if role.id in role_sets[set_name]["watch_roles"]:
                    role_sets[set_name]["watch_roles"].remove(role.id)
                    removed_roles.append(role.name)
            if removed_roles:
                await ctx.send(f"Roles {', '.join(removed_roles)} removed from the watch list for set '{set_name}'.")
            else:
                await ctx.send("No roles were removed from the watch list.")

    @rolereplace.command()
    async def addroles(self, ctx, set_name: str, *roles: discord.Role):
        """Add roles to the list of roles to replace in a specific set."""
        async with self.config.guild(ctx.guild).role_sets() as role_sets:
            if set_name not in role_sets:
                await ctx.send(f"No role set with the name '{set_name}' exists.")
                return
            added_roles = []
            for role in roles:
                if role.id not in role_sets[set_name]["replace_roles"]:
                    role_sets[set_name]["replace_roles"].append(role.id)
                    added_roles.append(role.name)
            if added_roles:
                await ctx.send(f"Roles {', '.join(added_roles)} added to the replacement list for set '{set_name}'.")
            else:
                await ctx.send("No new roles were added to the replacement list.")

    @rolereplace.command()
    async def removeroles(self, ctx, set_name: str, *roles: discord.Role):
        """Remove roles from the list of roles to replace in a specific set."""
        async with self.config.guild(ctx.guild).role_sets() as role_sets:
            if set_name not in role_sets:
                await ctx.send(f"No role set with the name '{set_name}' exists.")
                return
            removed_roles = []
            for role in roles:
                if role.id in role_sets[set_name]["replace_roles"]:
                    role_sets[set_name]["replace_roles"].remove(role.id)
                    removed_roles.append(role.name)
            if removed_roles:
                await ctx.send(f"Roles {', '.join(removed_roles)} removed from the replacement list for set '{set_name}'.")
            else:
                await ctx.send("No roles were removed from the replacement list.")

    @rolereplace.command()
    async def list(self, ctx):
        """List all role sets with their watched roles and roles to replace."""
        role_sets = await self.config.guild(ctx.guild).role_sets()

        if not role_sets:
            await ctx.send("There are no role sets configured.")
            return

        embed = discord.Embed(title="Role Sets", color=discord.Color.blue())
        for set_name, roles in role_sets.items():
            watch_roles = [ctx.guild.get_role(role_id) for role_id in roles["watch_roles"] if ctx.guild.get_role(role_id)]
            replace_roles = [ctx.guild.get_role(role_id) for role_id in roles["replace_roles"] if ctx.guild.get_role(role_id)]

            watch_roles_str = ", ".join([role.name for role in watch_roles]) if watch_roles else "None"
            replace_roles_str = ", ".join([role.name for role in replace_roles]) if replace_roles else "None"

            embed.add_field(name=f"Set: {set_name}", value=f"**Watched Roles:** {watch_roles_str}\n**Roles to Replace:** {replace_roles_str}", inline=False)

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        guild = after.guild
        role_sets = await self.config.guild(guild).role_sets()

        for set_name, roles in role_sets.items():
            watch_roles = roles["watch_roles"]
            replace_roles = roles["replace_roles"]

            new_roles = [guild.get_role(role_id) for role_id in watch_roles if guild.get_role(role_id) in after.roles and guild.get_role(role_id) not in before.roles]
            for new_role in new_roles:
                roles_to_remove = [guild.get_role(role_id) for role_id in replace_roles if guild.get_role(role_id) in after.roles]
                if roles_to_remove:
                    await after.remove_roles(*roles_to_remove, reason="RoleReplace: Replacing old roles with the new role")
                    await after.add_roles(new_role, reason="RoleReplace: Adding the new role")
                    self.log_role_change(after, new_role, roles_to_remove, set_name)

    def log_role_change(self, member: discord.Member, new_role: discord.Role, removed_roles: list, set_name: str):
        """Log the role changes in the console."""
        removed_roles_names = [role.name for role in removed_roles]
        removed_roles_str = ", ".join(removed_roles_names)
        log.info(f"[{set_name}] Member {member} had roles {removed_roles_str} replaced with {new_role.name}")

def setup(bot: Red):
    bot.add_cog(RoleReplace(bot))
