from redbot.core import commands

class Guest(commands.Cog, name="Guest"):
    """Receives Guest Commands(s)"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command() ### corrected by Flame
    async def _role(ctx, role: discord.Role):
        if role in ctx.author.roles:
            ctx.author.remove_roles(role)
            
        #ctx.author.remove_roles(role)

  def setup(bot: commands.Bot):
      bot.add_cog(Guest(bot))
