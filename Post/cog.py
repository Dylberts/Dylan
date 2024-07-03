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
    async def msg(self, ctx, *, message: str):
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
    async def forum(self, ctx, title: str, *, content: str = ""):
        """Create a new thread in the forum channel"""
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

        embed = discord.Embed(title=title, description=content, color=0x6EDFBA)
        type_msg = await ctx.send(
            "How would you like to post your message?\n\n"
            "React with 📝 for a simple message.\n"
            "React with 📜 for an embed."
        )
        await type_msg.add_reaction('📝')
        await type_msg.add_reaction('📜')

        def check_type(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['📝', '📜']

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check_type)
            if str(reaction.emoji) == '📝':
                confirm_msg = await ctx.send(f"Please confirm your forum post as a simple message: {content}")
            elif str(reaction.emoji) == '📜':
                confirm_msg = await ctx.send("Please confirm your forum post as an embed:", embed=embed)
            await confirm_msg.add_reaction('✅')
            await confirm_msg.add_reaction('❌')

            def check_confirm(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ['✅', '❌']

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check_confirm)
                if str(reaction.emoji) == '✅':
                    if str(reaction.emoji) == '📝':
                        thread = await forum_channel.create_thread(name=title, auto_archive_duration=1440)
                        await thread.send(content=content)
                        await ctx.send(f"Thread created with message in {thread.mention}!", delete_after=10)
                    elif str(reaction.emoji) == '📜':
                        thread = await forum_channel.create_thread(name=title, auto_archive_duration=1440)
                        await thread.send(embed=embed)
                        await ctx.send(f"Thread created with embed in {thread.mention}!", delete_after=10)
                elif str(reaction.emoji) == '❌':
                    await ctx.send("Forum post canceled. You can retype the message to edit it.", delete_after=10)
            except asyncio.TimeoutError:
                await ctx.send("You took too long to respond. Forum post canceled.", delete_after=10)

        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Forum post canceled.", delete_after=10)

        await type_msg.delete()
        await ctx.message.delete()

def setup(bot):
    bot.add_cog(Post(bot))
