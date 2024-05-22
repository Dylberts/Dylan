from redbot.core import commands
import discord

class RoleLock(commands.Cog, name="RoleLock"):
    def __init__(self, bot):
        self.bot = bot
        self.locked_roles = {
            # @Age (13-17): [Blocked Roles: @Age (18-25), @Age (26-35), @Age (26-35), @Age (36-48+), @NSFW]
            1233366060477186048: [1233366502451712074, 1233366641572712520, 1233366931302776843],
            # All role ID's nested are in the order listed
        }

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        for locked_role_id, blocked_role_ids in self.locked_roles.items():
            if locked_role_id in [role.id for role in after.roles]:
                for role in after.roles:
                    if role.id in blocked_role_ids:
                        await after.remove_roles(role)
                        
class RoleReplace(commands.Cog, name="RoleReplace"):
    def __init__(self, bot, channel_id):
        self.bot = bot
        self.channel_id = channel_id
        self.role_replacements = {
            # Format: {current_role_id: new_role_id}
            1235573502459904042: 1235798008126246983,
            # Add more role replacements as needed
        }
        self.emoji_to_role_id = {
            "🥇": 1235573502459904042,  # Example mapping
            "🥈": 1235798008126246983,  # Example mapping
            "🥉": 1235798803425132624,
            "1️⃣": 1233254368963334185,
            "2️⃣": 1233254790406869005,
            "3️⃣": 1233255218817404938,
            "4️⃣": 1233256062946246666,
            "5️⃣": 1233256207112732812,
            "6️⃣": 1233256301660864554,
            "7️⃣": 1233256478228484116,
            "8️⃣": 1233256570247188510,
            # Add more mappings as needed
        }

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.handle_reaction(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.handle_reaction(payload)

    async def handle_reaction(self, payload):
        if payload.guild_id != self.channel_id:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            return

        role_id = self.emoji_to_role_id.get(str(payload.emoji))
        if role_id is None:
            return

        await self.replace_role(member, role_id)

    async def replace_role(self, member, new_role_id):
        roles_to_remove = [role_id for role_id, replacement_id in self.role_replacements.items() if replacement_id == new_role_id]
        
        for role_id in roles_to_remove:
            role = discord.utils.get(member.guild.roles, id=role_id)
            if role and role in member.roles:
                await member.remove_roles(role)

        new_role = discord.utils.get(member.guild.roles, id=new_role_id)
        if new_role and new_role not in member.roles:
            await member.add_roles(new_role)
                        
def setup(bot):
    bot.add_cog(RoleLock(bot))
    bot.add_cog(RoleReplace(bot, channel_id=1217776121274175499))
