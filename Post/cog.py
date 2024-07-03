from redbot.core import commands, Config, checks
import discord

class Post(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "forum_channel": None,
        }
        self.config.register_guild(**default_guild)

    @commands.group()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def post(self, ctx):
        """Post commands"""
        pass

    @post.command()
    async def setforum(self, ctx, channel: discord.ForumChannel):
        """Set the forum channel"""
        await self.config.guild(ctx.guild).forum_channel.set(channel.id)
        await ctx.send(f"Forum channel set to {channel.mention}")

    @post.command()
    async def forum(self, ctx, title: str, *, content: str):
        """Create a new thread in the forum channel"""
        channel_id = await self.config.guild(ctx.guild).forum_channel()
        if not channel_id:
            await ctx.send("Forum channel not set. Use `post setforum` to set it.")
            return

        forum_channel = ctx.guild.get_channel(channel_id)
        if not forum_channel:
            await ctx.send("Forum channel not found.")
            return

        if not content:
            await ctx.send("Content cannot be empty.")
            return

        # Create the thread with the provided title
        try:
            thread = await forum_channel.create_thread(name=title, auto_archive_duration=1440)
        except discord.HTTPException as e:
            await ctx.send(f"Failed to create thread: {e}")
            return

        # Send the content to the created thread
        try:
            await thread.send(content)
            await ctx.send(f"Thread created in {thread.mention}!")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to send message to thread: {e}")
            return

async def setup(bot):
    bot.add_cog(Post(bot))
