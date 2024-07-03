import asyncio
import discord
from redbot.core import commands, Config, checks

class Post(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "post_channel": None,
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
    async def setchannel(self, ctx, channel: discord.TextChannel):
        """Set the post channel"""
        await self.config.guild(ctx.guild).post_channel.set(channel.id)
        msg = await ctx.send(f"Post channel set to {channel.mention}")
        await msg.delete(delay=10)

    @post.command()
    async def say(self, ctx, *, message: str):
        """Make a post"""
        channel_id = await self.config.guild(ctx.guild).post_channel()
        if not channel_id:
            msg = await ctx.send("Post channel not set. Use `post setchannel` to set it.")
            await msg.delete(delay=10)
            return

        embed = discord.Embed(description=message, color=0x6EDFBA)
        confirm_msg = await ctx.send("Please confirm your post:", embed=embed)
        await confirm_msg.add_reaction('✅')
        await confirm_msg.add_reaction('❌')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌']

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            if str(reaction.emoji) == '✅':
                channel = self.bot.get_channel(channel_id)
                await channel.send(embed=embed)
                await ctx.send("Post sent!", delete_after=10)
            elif str(reaction.emoji) == '❌':
                await ctx.send("Post canceled. You can retype the message to edit it.", delete_after=10)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Post canceled.", delete_after=10)

        await confirm_msg.delete()
        await ctx.message.delete()

    @post.command()
    async def setforum(self, ctx, channel: discord.ForumChannel):
        """Set the forum channel"""
        await self.config.guild(ctx.guild).forum_channel.set(channel.id)
        msg = await ctx.send(f"Forum channel set to {channel.mention}")
        await msg.delete(delay=10)

    @post.command()
    async def forumpost(self, ctx, thread_id: int, title: str, *, content: str = ""):
        """Create a post in an existing forum thread"""
        channel_id = await self.config.guild(ctx.guild).forum_channel()
        if not channel_id:
            msg = await ctx.send("Forum channel not set. Use `post setforum` to set it.")
            await msg.delete(delay=10)
            return
        
        forum_channel = self.bot.get_channel(channel_id)
        if not forum_channel:
            msg = await ctx.send("Forum channel not found.")
            await msg.delete(delay=10)
            return

        thread = discord.utils.get(forum_channel.threads, id=thread_id)
        if not thread:
            msg = await ctx.send("Thread not found.")
            await msg.delete(delay=10)
            return

        embed = discord.Embed(title=title, description=content, color=0x6EDFBA)
        confirm_msg = await ctx.send("Please confirm your forum post:", embed=embed)
        await confirm_msg.add_reaction('✅')
        await confirm_msg.add_reaction('❌')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌']

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            if str(reaction.emoji) == '✅':
                await thread.create_post(title=title, content=content)
                await ctx.send(f"Post created in thread {thread.name}!", delete_after=10)
            elif str(reaction.emoji) == '❌':
                await ctx.send("Forum post canceled. You can retype the message to edit it.", delete_after=10)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Forum post canceled.", delete_after=10)

        await confirm_msg.delete()
        await ctx.message.delete()

def setup(bot):
    bot.add_cog(Post(bot))
