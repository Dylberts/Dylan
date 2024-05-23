import discord
from redbot.core import commands, Config
from redbot.core.bot import Red

class RoleReplace(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Replace with a unique identifier
        default_guild = {"role_sets": {}}
        self.config.register_guild(**default_guild)
    
    @commands.group()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def rolereplace(self, ctx):
        """Manage RoleReplace settings."""
        pass

    @rolereplace.command()
    async def addset(self, ctx, set_name: str):
        """Add a new role set."""
        async with self.config.guild(ctx.guild).role_sets() as role_sets:
            if set_name in role_sets:
                await ctx.send(f"A role set with the name '{set_name}' already exists.")
            else:
                role_sets[set_name] = []
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
    async def addroles(self, ctx, set_name: str, *roles: discord.Role):
        """Add roles to a specific set."""
        async with self.config.guild(ctx.guild).role_sets() as role_sets:
            if set_name not in role_sets:
                await ctx.send(f"No role set with the name '{set_name}' exists.")
                return
            added_roles = []
            for role in roles:
                if role.id not in role_sets[set_name]:
                    role_sets[set_name].append(role.id)
                    added_roles.append(role.name)
            if added_roles:
                await ctx.send(f"Roles {', '.join(added_roles)} added to set '{set_name}'.")
            else:
                await ctx.send("No new roles were added to the set.")

    @rolereplace.command()
    async def removeroles(self, ctx, set_name: str, *roles: discord.Role):
        """Remove roles from a specific set."""
        async with self.config.guild(ctx.guild).role_sets() as role_sets:
            if set_name not in role_sets:
                await ctx.send(f"No role set with the name '{set_name}' exists.")
                return
            removed_roles = []
            for role in roles:
                if role.id in role_sets[set_name]:
                    role_sets[set_name].remove(role.id)
                    removed_roles.append(role.name)
            if removed_roles:
                await ctx.send(f"Roles {', '.join(removed_roles)} removed from set '{set_name}'.")
            else:
                await ctx.send("No roles were removed from the set.")

    @rolereplace.command()
    async def list(self, ctx):
        """List all role sets with their roles."""
        role_sets = await self.config.guild(ctx.guild).role_sets()

        if not role_sets:
            await ctx.send("There are no role sets configured.")
            return

        embed = discord.Embed(title="Role Sets", color=0x6EDFBA)
        for set_name, role_ids in role_sets.items():
            roles = [ctx.guild.get_role(role_id) for role_id in role_ids if ctx.guild.get_role(role_id)]
            roles_str = ", ".join([role.name for role in roles]) if roles else "None"
            embed.add_field(name=f"Set: {set_name}", value=f"**Roles:** {roles_str}", inline=False)

        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Detect if a role was added
        added_roles = set(after.roles) - set(before.roles)
        if added_roles:
            for role in added_roles:
                await self._handle_role_addition(after, role)
    
    async def _handle_role_addition(self, member, added_role):
        guild = member.guild
        role_sets = await self.config.guild(guild).role_sets()
        
        for set_name, role_ids in role_sets.items():
            if added_role.id in role_ids:
                roles_to_remove = [guild.get_role(role_id) for role_id in role_ids if role_id != added_role.id and guild.get_role(role_id) in member.roles]
                if roles_to_remove:
                    await member.remove_roles(*roles_to_remove, reason=f"RoleReplace: Assigned {added_role.name}")

def setup(bot: Red):
    bot.add_cog(RoleReplace(bot))
