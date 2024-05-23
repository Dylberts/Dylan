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
            "role_sets": {},
            "role_reactions": {}  # Track messages and their role reactions
        }
        self.config.register_guild(**default_guild)
    
    @commands.group()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def rolereplace(self, ctx):
        """Manage RoleReplace settings."""
        pass  # Do nothing if no subcommand is invoked

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
                    await self._remove_role_reactions(ctx.guild, role)
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

    @rolereplace.command()
    async def addreaction(self, ctx, message_id: int, emoji: str, role: discord.Role):
        """Associate a role with an emoji reaction on a specific message."""
        async with self.config.guild(ctx.guild).role_reactions() as role_reactions:
            if message_id not in role_reactions:
                role_reactions[message_id] = {}
            role_reactions[message_id][emoji] = role.id
            await ctx.send(f"Reaction {emoji} on message ID {message_id} now grants the role {role.name}.")

    @rolereplace.command()
    async def removereaction(self, ctx, message_id: int, emoji: str):
        """Remove the association of a role with an emoji reaction on a specific message."""
        async with self.config.guild(ctx.guild).role_reactions() as role_reactions:
            if message_id in role_reactions and emoji in role_reactions[message_id]:
                del role_reactions[message_id][emoji]
                await ctx.send(f"Reaction {emoji} on message ID {message_id} no longer grants any role.")
            else:
                await ctx.send("No such reaction-role association exists.")
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Detect if a role was added
        added_roles = set(after.roles) - set(before.roles)
        if added_roles:
            for role in added_roles:
                await self._handle_role_addition(after, role)
        # Detect if a role was removed
        removed_roles = set(before.roles) - set(after.roles)
        if removed_roles:
            for role in removed_roles:
                await self._handle_role_removal(after, role)
    
    async def _handle_role_addition(self, member, added_role):
        guild = member.guild
        role_sets = await self.config.guild(guild).role_sets()
        
        for set_name, role_ids in role_sets.items():
            if added_role.id in role_ids:
                roles_to_remove = [guild.get_role(role_id) for role_id in role_ids if role_id != added_role.id and guild.get_role(role_id) in member.roles]
                if roles_to_remove:
                    await member.remove_roles(*roles_to_remove, reason=f"RoleReplace: Assigned {added_role.name}")

    async def _handle_role_removal(self, member, removed_role):
        await self._remove_role_reactions_from_member(member, removed_role)
    
    async def _remove_role_reactions_from_member(self, member, role):
        """Remove reactions corresponding to the role being removed."""
        guild = member.guild
        role_reactions = await self.config.guild(guild).role_reactions()

        for message_id, reactions in role_reactions.items():
            for emoji, role_id in reactions.items():
                if role_id == role
