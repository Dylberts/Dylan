from redbot.core import commands, Config, checks
import discord

class Post(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "forum_channel": None,
            "thread_channel": None,
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
    async def setthread(self, ctx, channel: discord.TextChannel):
        """Set the thread channel"""
        await self.config.guild(ctx.guild).thread_channel.set(channel.id)
        await ctx.send(f"Thread channel set to {channel.mention}")

    @post.command()
    async def forum(self, ctx, title: str, *, description: str = None):
        """Create a new thread in the forum channel"""
        channel_id = await self.config.guild(ctx.guild).forum_channel()
        if not channel_id:
            await ctx.send("Forum channel not set. Use `post setforum` to set it.")
            return

        forum_channel = ctx.guild.get_channel(channel_id)
        if not forum_channel:
            await ctx.send("Forum channel not found.")
            return

        # Create the thread with the provided title and optional description in the forum channel
        thread = await forum_channel.create_thread(name=title, content=description, auto_archive_duration=1440)
        embed = discord.Embed(
            title="Forum Thread Created",
            description=f"[Click here to view it](https://discord.com/channels/{ctx.guild.id}/{forum_channel.id}/{thread.id})",
            color=0x6EDFBA
        )
        await ctx.send(embed=embed)

    @post.command()
    async def thread(self, ctx, title: str, *, message: str = None):
        """Create a new thread in the specified thread channel"""
        channel_id = await self.config.guild(ctx.guild).thread_channel()
        if not channel_id:
            await ctx.send("Thread channel not set. Use `post setthread` to set it.")
            return

        thread_channel = ctx.guild.get_channel(channel_id)
        if not thread_channel:
            await ctx.send("Thread channel not found.")
            return

        # Send the initial message (if provided) and create a thread in the specified text channel
        if message:
            msg = await thread_channel.send(message)
            thread = await msg.create_thread(name=title, auto_archive_duration=1440)
        else:
            # If no message is provided, create an empty thread
            thread = await thread_channel.create_thread(name=title, auto_archive_duration=1440)
            
        embed = discord.Embed(
            title="Thread Created",
            description=f"[Click here to view it](https://discord.com/channels/{ctx.guild.id}/{thread_channel.id}/{thread.id})",
            color=0x6EDFBA
        )
        await ctx.send(embed=embed)

async def setup(bot):
    bot.add_cog(Post(bot))
