from redbot.core import commands
import discord

class Guest(commands.Cog, name="Guest"):
    """Receives Guest Commands(s)"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="guest", hidden=True)
    async def remove_my_tole(self, ctx, role_id: int="1240961142554234970u"):
        #role = discord.utils.get(ctx.guild.roles, id=role_id)
        role = discord.utils.get(ctx.guild.roles, id=role_id)
        if role:
            await ctx.author.remove_roles(role)
            await ctx.message.delete() #silent

def setup(bot):
    bot.add_cog(Guest(bot))
