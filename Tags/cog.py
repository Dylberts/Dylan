import discord
from redbot.core import commands

class Tags(commands.Cog):
    """A simple cog for Red Bot with a button link"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def tiermaker(self, ctx):
        """Responds with a friendly message and a button link"""
        button = discord.ui.Button(label="Create Tiermaker", url="https://tiermaker.com/create/isekai-slow-life-fellows-16506986")

        view = discord.ui.View()
        view.add_item(button)

        await ctx.send("Hello! How can I assist you today?", view=view)

async def setup(bot):
    await bot.add_cog(Tags(bot))
