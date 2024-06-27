import discord
from redbot.core import commands
from redbot.core.bot import Red

class Tags(commands.Cog):
    """Simple tag commands will be created here"""

    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command()
    async def tiermaker(self, ctx: commands.Context):
        """Responds with an embed image and a button link"""
        button = discord.ui.Button(
            label="Create Tiermaker", 
            url="https://tiermaker.com/create/isekai-slow-life-fellows-16506986"
        )

        view = discord.ui.View()
        view.add_item(button)

        embed = discord.Embed(color=discord.Color(0x6EDFBA))
        embed.set_image(url="https://i.postimg.cc/zvgYjQp9/IMG-8698.jpg")  # Replace with your image URL

        await ctx.send(embed=embed, view=view)

async def setup(bot: Red):
    await bot.add_cog(Tags(bot))
