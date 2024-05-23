import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
import logging

log = logging.getLogger("red.RoleReplace")

class RoleReplace(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "role_sets": {},
            "reaction_roles": {}  # New config entry for tracking reaction roles
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

    @rolereplace.command()
    async def addreactionrole(self, ctx, message_id: int, emoji: str, role: discord.Role):
        """Add a reaction role to the tracking list."""
        async with self.config.guild(ctx.guild).reaction_roles() as reaction_roles:
            reaction_roles[str(role.id)] = {
                "message_id": message_id,
                "emoji": emoji,
                "channel_id": ctx.channel.id  # Track the channel ID as well
            }
            await ctx.send(f"Reaction role tracking added for role {role.name} with emoji {emoji} on message {message_id}.")

    async def _remove_role_reactions(self, guild, role):
        log.info(f"Entering _remove_role_reactions for role {role.name} ({role.id}) in guild {guild.name} ({guild.id})")
        reaction_roles = await self.config.guild(guild).reaction_roles()
        role_info = reaction_roles.get(str(role.id))
        
        if role_info:
            message_id = role_info["message_id"]
            emoji = role_info["emoji"]
            channel_id = role_info["channel_id"]

            log.info(f"Found reaction role info for role {role.name}: message_id={message_id}, emoji={emoji}, channel_id={channel_id}")

            channel = guild.get_channel(channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(message_id)
                    reaction = discord.utils.get(message.reactions, emoji=emoji)
                    if reaction:
                        async for user in reaction.users():
                            if user != self.bot.user:
                                log.info(f"Removing reaction for user {user} from message {message_id} with emoji {emoji}")
                                await reaction.remove(user)
                    else:
                        log.warning(f"No reaction found with emoji {emoji} on message {message_id}")
                except discord.NotFound:
                    log.warning(f"Message with ID {message_id} not found in channel {channel_id}")
            else:
                log.warning(f"Channel with ID {channel_id} not found")
        else:
            log.warning(f"No reaction role info found for role {role.name} ({role.id})")
        log.info(f"Exiting _remove_role_reactions for role {role.name} ({role.id}) in guild {guild.name} ({guild.id})")

def setup(bot: Red):
    bot.add_cog(RoleReplace(bot))
