import discord
from redbot.core import commands
from redbot.core.bot import Red

class Tags(commands.Cog):
    """A simple cog for Red Bot with button links"""

    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command()
    async def tiermaker(self, ctx: commands.Context):
        """Responds with a friendly message and button links"""
        button1 = discord.ui.Button(
            label="Family List", 
            url="https://tiermaker.com/create/isekai-slow-life-familiars-16506986"
        )
        
        button2 = discord.ui.Button(
            label="Fellow List", 
            url="https://tiermaker.com/create/isekai-slow-life-fellows-16506986"
        )
        
        view = discord.ui.View()
        view.add_item(button1)
        view.add_item(button2)

        embed = discord.Embed(color=discord.Color(0x6EDFBA))
        embed.set_image(url="https://i.postimg.cc/zvgYjQp9/IMG-8698.jpg")  # Replace with your image URL

        await ctx.send(embed=embed, view=view)

async def setup(bot: Red):
    await bot.add_cog(Tags(bot))
