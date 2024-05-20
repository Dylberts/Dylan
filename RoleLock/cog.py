from redbot.core import commands
import discord

class RoleLock(commands.Cog, name="RoleLock"):
    def __init__(self, bot):
        self.bot = bot
        self.locked_role_id = 1233366060477186048  # @Age (13-17) Role ID > Replace with the ID of the role you want to lock
        self.blocked_role_ids = [1233366502451712074, 1233366641572712520, 1233366931302776843, 1233369491447091251]  # @Age (18-25), @Age (26-35), @Age (36-48+), @NSFW Role ID > Replace with the ID of the role you want to block 

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        for role in after.roles:
            if role.id in self.blocked_role_ids and self.locked_role_id in [role.id for role in after.roles]:
                await after.remove_roles(role)
                #await after.send("You cannot obtain this role while having the locked 
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        guild = message.guild
        member = guild.get_member(payload.user_id)
        
        if member:
            if self.locked_role_id in [role.id for role in member.roles]:
                emoji_id = str(payload.emoji.id)
                if emoji_id in ["1233366502451712074", "1233366641572712520", "1233366931302776843", "1233369491447091251"]: # @Age (18-25), @Age (26-35), @Age (36-48+), @NSFW > Replace with your emoji IDs
                    await message.remove_reaction(payload.emoji, member)

def setup(bot):
   bot.add_cog(RoleLock(bot))
