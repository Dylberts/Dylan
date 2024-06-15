import discord
from redbot.core import commands
import random
import asyncio

class Quote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="quote")
    async def random_quote(self, ctx):
        channels = [channel for channel in ctx.guild.text_channels if channel.permissions_for(ctx.guild.me).read_message_history]
        messages = []

        for channel in channels:
            async for message in channel.history(limit=500):
                if message.author.bot:
                    continue
                messages.append(message)
        
        if not messages:
            await ctx.send("No quotes found.")
            return

        message = random.choice(messages)
        embed = discord.Embed(description=message.content, color=0x6EDFBA)
        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
        
        await ctx.send(embed=embed)

    @commands.command(name="rquote")
    async def random_funny_quote(self, ctx):
        users = [member.display_name for member in ctx.guild.members if not member.bot]
        quotes = [
            "Life is like a box of chocolates. You never know what you're gonna get.",
            "I'm not arguing, I'm just explaining why I'm right.",
            "The early bird can have the worm, because worms are gross and mornings are stupid.",
            "I'm on a seafood diet. I see food, and I eat it.",
            "I would challenge you to a battle of wits, but I see you are unarmed."
        ]

        compliments = [
            "You're a great person, {user}!",
            "{user}, you light up the room!",
            "You're awesome, {user}!",
        ]

        insults = [
            "{user}, you're like a cloud. When you disappear, it's a beautiful day.",
            "I'd agree with you {user}, but then we'd both be wrong.",
            "{user}, if I had a dollar for every time you said something smart, I'd be broke.",
        ]

        if users:
            user = random.choice(users)
            choice = random.choice(quotes + [compliment.format(user=user) for compliment in compliments] + [insult.format(user=user) for insult in insults])
        else:
            choice = random.choice(quotes)

        embed = discord.Embed(description=choice, color=0x6EDFBA)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Quote(bot))
