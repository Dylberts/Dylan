from redbot.core import commands
import discord

class Guest(commands.Cog, name="Guest"):
    """Receives Guest Commands(s)"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def _role(ctx, role: discord.Role):
        if role in ctx.author.roles:
            await ctx.send("")            
        ctx.author.remove_roles(role)
