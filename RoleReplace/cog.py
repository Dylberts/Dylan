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

    async def _remove_role_reactions(self, guild: discord.Guild, role: discord.Role):
        """Remove reactions associated with a role from all reaction role messages."""
        roletools = self.bot.get_cog("RoleTools")
            if not roletools:
                log.warning("RoleTools cog is not loaded.")
        return

    try:
        reaction_roles = await roletools.config.guild(guild).reaction_roles()
        if isinstance(reaction_roles, dict):
            for message_id, reactions in reaction_roles.items():
                if isinstance(reactions, dict):
                    for emoji, role_id in reactions.items():
                        if role_id == role.id:
                            message = await self._fetch_message(guild, message_id)
                            if message:
                                await self._remove_role_reaction(message, emoji, role)
        else:
            log.warning("Invalid reaction roles data structure.")
    except Exception as e:
        log.error(f"Error accessing RoleTools config: {e}")

    async def _fetch_message(self, guild: discord.Guild, message_id: int):
        """Fetch a message by ID from the guild."""
        for channel in guild.text_channels:
            try:
                message = await channel.fetch_message(message_id)
                if message:
                    return message
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                continue
        return None

    async def _remove_role_reaction(self, message: discord.Message, emoji: str, role: discord.Role):
        """Remove a user's reaction associated with a role from a message."""
        for reaction in message.reactions:
            if str(reaction.emoji) == emoji:
                async for user in reaction.users():
                    member = message.guild.get_member(user.id)
                    if member and role in member.roles:
                        await message.remove_reaction(emoji, user)

def setup(bot: Red):
    bot.add_cog(RoleReplace(bot))
