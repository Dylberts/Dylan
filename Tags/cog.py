import discord
from redbot.core import commands
from redbot.core.bot import Red

class Tags(commands.Cog):
    """A simple cog for Red Bot with a button link"""

    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command()
    async def tiermaker(self, ctx: commands.Context):
        """Responds with a friendly message and a button link"""
        button = discord.ui.Button(label="Create Tiermaker", url="https://tiermaker.com/create/isekai-slow-life-fellows-16506986")

        view = discord.ui.View()
        view.add_item(button)

        await ctx.send("Hello! How can I assist you today?", view=view)

async def setup(bot: Red):
    await bot.add_cog(Tags(bot))
