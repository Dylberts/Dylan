import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
import asyncio

class RoleReplace(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Replace with a unique identifier
        default_guild = {
            "role_sets": {},
            "reaction_settings": {
                "role_emoji_mapping": {},  # Maps role IDs to emoji strings
                "messages": {}  # Maps channel IDs to lists of message IDs
            }
        }
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
        """List all role sets with their roles and emoji-role mappings."""
        role_sets = await self.config.guild(ctx.guild).role_sets()
        reaction_settings = await self.config.guild(ctx.guild).reaction_settings()
        role_emoji_mapping = reaction_settings["role_emoji_mapping"]
        messages = reaction_settings["messages"]

        if not role_sets and not role_emoji_mapping and not messages:
            await ctx.send("There are no role sets, emoji-role mappings, or message settings configured.")
            return

        embed = discord.Embed(title="📋 Role Replace Settings", color=0x6EDFBA)

        if role_sets:
            for set_name, role_ids in role_sets.items():
                roles = [ctx.guild.get_role(role_id) for role_id in role_ids if ctx.guild.get_role(role_id)]
                roles_str = ", ".join([role.name for role in roles]) if roles else "None"
                embed.add_field(name=f"🗂️ Set: {set_name}", value=f"**Roles:** {roles_str}", inline=False)

        if role_emoji_mapping:
            for role_id, emoji in role_emoji_mapping.items():
                role = ctx.guild.get_role(int(role_id))
                if role:
                    embed.add_field(name=f"🎭 Role: {role.name}", value=f"**Emoji:** {emoji}", inline=False)
                else:
                    embed.add_field(name=f"🎭 Role ID: {role_id}", value=f"**Emoji:** {emoji}", inline=False)

        if messages:
            for channel_id, message_ids in messages.items():
                channel = ctx.guild.get_channel(int(channel_id))
                if channel:
                    message_ids_str = ", ".join(map(str, message_ids))  # Convert each message ID to string
                    embed.add_field(name=f"💬 Channel: {channel.name}", value=f"**Messages:** {message_ids_str}", inline=False)

        embed.set_footer(text="RoleReplace Settings")
        await ctx.send(embed=embed)
        
    @rolereplace.command()
    async def assignemoji(self, ctx, role: discord.Role, emoji: str):
        """Assign an emoji to a role for reaction removal."""
        async with self.config.guild(ctx.guild).reaction_settings() as settings:
            settings["role_emoji_mapping"][str(role.id)] = emoji
            await ctx.send(f"Emoji {emoji} assigned to role {role.name} for reaction removal.")

    @rolereplace.command()
    async def removeemoji(self, ctx, role: discord.Role):
        """Remove an assigned emoji from a role."""
        async with self.config.guild(ctx.guild).reaction_settings() as settings:
            if str(role.id) in settings["role_emoji_mapping"]:
                del settings["role_emoji_mapping"][str(role.id)]
                await ctx.send(f"Emoji assignment removed from role {role.name}.")
            else:
                await ctx.send(f"No emoji assignment found for role {role.name}.")

    @rolereplace.command()
    async def addmessage(self, ctx, channel: discord.TextChannel, *message_ids: int):
        """Add messages to the reaction removal list."""
        async with self.config.guild(ctx.guild).reaction_settings() as settings:
            if str(channel.id) not in settings["messages"]:
                settings["messages"][str(channel.id)] = list(message_ids)
            else:
                settings["messages"][str(channel.id)].extend(message_ids)
            await ctx.send(f"Message IDs {', '.join(map(str, message_ids))} in channel {channel.mention} added to the reaction removal list.")

    @rolereplace.command()
    async def removemessage(self, ctx, channel: discord.TextChannel, *message_ids: int):
        """Remove messages from the reaction removal list."""
        async with self.config.guild(ctx.guild).reaction_settings() as settings:
            if str(channel.id) in settings["messages"]:
                for message_id in message_ids:
                    if message_id in settings["messages"][str(channel.id)]:
                        settings["messages"][str(channel.id)].remove(message_id)
                await ctx.send(f"Message IDs {', '.join(map(str, message_ids))} in channel {channel.mention} removed from the reaction removal list.")
            else:
                await ctx.send(f"No messages found in channel {channel.mention}.")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Detect if a role was added or removed
        added_roles = set(after.roles) - set(before.roles)
        removed_roles = set(before.roles) - set(after.roles)

        if added_roles:
            for role in added_roles:
                await self._handle_role_addition(after, role)
        
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
        guild = member.guild
        settings = await self.config.guild(guild).reaction_settings()
    
        role_emoji_mapping = settings["role_emoji_mapping"]
        if str(removed_role.id) not in role_emoji_mapping:
            return

        emoji_to_check = role_emoji_mapping[str(removed_role.id)]
        for channel_id_str, message_ids in settings["messages"].items():
            channel = guild.get_channel(int(channel_id_str))
            if not channel:
                continue

            if isinstance(message_ids, int):
                message_ids = [message_ids]  # Convert to a list for uniform handling
            
            for message_id in message_ids:
                try:
                    message = await channel.fetch_message(message_id)
                except discord.NotFound:
                    continue
            
                for reaction in message.reactions:
                    if str(reaction.emoji) == emoji_to_check:
                        async for user in reaction.users():
                            if member == user:
                                await message.remove_reaction(reaction.emoji, user)
                                break

def setup(bot: Red):
    bot.add_cog(RoleReplace(bot))
