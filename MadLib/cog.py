import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import bold
import random
from .madlibs import MADLIBS

class MadLib(commands.Cog):
    """MadLibs game for Discord"""

    def __init__(self, bot):
        self.bot = bot
        self.current_game = None

    @commands.group(aliases=['ml'])
    async def madlib(self, ctx):
        """MadLibs game menu"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid MadLib command. Use `!madlib start` or `!madlib end`.")

    @madlib.command(aliases=['startml'])
    async def start(self, ctx):
        """Start a new MadLib game."""
        if self.current_game:
            await ctx.send("A MadLib game is already in progress.")
            return
        
        template = random.choice(MADLIBS)
        self.current_game = {
            "template": template["template"],
            "placeholders": template["placeholders"],
            "title": template["title"],
            "responses": [],
            "channel": ctx.channel,
            "author": ctx.author
        }

        await ctx.send(f"Starting a new MadLib: {bold(template['title'])}")
        await ctx.send(f"Please provide a(n) {self.current_game['placeholders'][0]}")

    @madlib.command(aliases=['endml'])
    async def end(self, ctx):
        """End the current MadLib game early."""
        if not self.current_game:
            await ctx.send("No MadLib game is currently in progress.")
            return
        
        filled_story = self.current_game["template"].format(*self.current_game["responses"])
        embed = discord.Embed(title="MadLib Ended Early", description=filled_story, color=0x6EDFBA)
        await ctx.send(embed=embed)
        self.current_game = None

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self.current_game or message.author.bot:
            return

        if message.channel == self.current_game['channel'] and message.author != self.current_game['author']:
            placeholder = self.current_game["placeholders"].pop(0)
            self.current_game["responses"].append(message.content)

            if self.current_game["placeholders"]:
                next_placeholder = self.current_game["placeholders"][0]
                await message.channel.send(f"Please provide a(n) {next_placeholder}")
            else:
                await self.complete_madlib(message.channel)

    async def complete_madlib(self, channel):
        filled_story = self.current_game["template"].format(*self.current_game["responses"])
        embed = discord.Embed(title="Completed MadLib", description=filled_story, color=0x6EDFBA)
        await channel.send(embed=embed)
        self.current_game = None

def setup(bot):
    bot.add_cog(MadLib(bot))
