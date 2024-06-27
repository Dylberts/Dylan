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
        button = discord.ui.Button(
            label="Create Tiermaker", 
            url="https://tiermaker.com/create/isekai-slow-life-fellows-16506986",
            style=discord.ButtonStyle.primary  # This sets the button color to blue
        )

        view = discord.ui.View()
        view.add_item(button)

        #embed = discord.Embed(description="Hello! How can I assist you today?")
        embed.set_image(url="https://imgur.com/a/l1Vt9Ry")  # Replace with your image URL

        await ctx.send(embed=embed, view=view)

async def setup(bot: Red):
    await bot.add_cog(Tags(bot))
