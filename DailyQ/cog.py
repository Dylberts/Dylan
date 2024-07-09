import discord
from redbot.core import commands, Config
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from datetime import datetime, timedelta
import pytz
import asyncio
from .Qlist import Qlist

class DailyQ(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "channel_id": None,
            "duration": 24,
            "specific_time": None,
            "timezone": "UTC",
            "question_limit": 3,
            "skip_votes_required": 3
        }
        self.config.register_guild(**default_guild)
        self.qlist = Qlist()
        self.current_skip_votes = 0
        self.skip_voters = set()
        self.next_question_time = None
        self.bot.loop.create_task(self.check_and_ask_question())

    async def check_and_ask_question(self):
        await self.bot.wait_until_red_ready()
        while True:
            now = datetime.now(pytz.utc)
            guilds = await self.config.all_guilds()
            for guild_id, settings in guilds.items():
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue
                channel = guild.get_channel(settings["channel_id"])
                if not channel:
                    continue
                specific_time = settings["specific_time"]
                if specific_time:
                    specific_time = datetime.strptime(specific_time, "%H:%M").time()
                    timezone = pytz.timezone(settings["timezone"])
                    target_time = datetime.combine(now.date(), specific_time)
                    target_time = timezone.localize(target_time).astimezone(pytz.utc)
                    if now >= target_time and (not self.next_question_time or now >= self.next_question_time):
                        await self.ask_question(channel)
                        self.next_question_time = now + timedelta(hours=settings["duration"])
                else:
                    if not self.next_question_time or now >= self.next_question_time:
                        await self.ask_question(channel)
                        self.next_question_time = now + timedelta(hours=settings["duration"])
            await asyncio.sleep(60)

    async def ask_question(self, channel):
        question = self.qlist.get_random_question()
        embed = discord.Embed(
            title="DAILY QUESTION 💬",
            description=f"> {question}",
            color=0x6EDFBA
        )
        embed.set_footer(text="Try `!q ask` to add your own daily questions")
        view = SkipVoteView(self)
        await channel.send(embed=embed, view=view)
        self.current_skip_votes = 0
        self.skip_voters = set()

    @commands.group(name="question", aliases=["q"])
    async def question(self, ctx):
        """Daily question commands"""
        pass

    @question.command(name="setchannel")
    @commands.admin_or_permissions(manage_guild=True)
    async def set_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel for the daily question"""
        await self.config.guild(ctx.guild).channel_id.set(channel.id)
        await ctx.send(f"Daily question channel set to {channel.mention}")

    @question.command(name="setduration")
    @commands.admin_or_permissions(manage_guild=True)
    async def set_duration(self, ctx, hours: int):
        """Set how often the daily question is asked (in hours)"""
        await self.config.guild(ctx.guild).duration.set(hours)
        await ctx.send(f"Daily question duration set to {hours} hours")

    @question.command(name="settime")
    @commands.admin_or_permissions(manage_guild=True)
    async def set_time(self, ctx, time: str, timezone: str = "UTC"):
        """Set the specific time for the daily question"""
        await self.config.guild(ctx.guild).specific_time.set(time)
        await self.config.guild(ctx.guild).timezone.set(timezone)
        await ctx.send(f"Daily question time set to {time} {timezone}")

    @question.command(name="ask")
    async def ask(self, ctx, *, question: str):
        """Submit a daily question"""
        user_questions = self.qlist.get_user_questions(ctx.author.id)
        question_limit = await self.config.guild(ctx.guild).question_limit()
        if len(user_questions) >= question_limit:
            await ctx.send("You have reached your daily question limit.", delete_after=10)
            return
        confirmation_message = await ctx.send(f"Do you want to submit this question? `{question}`")
        await confirmation_message.add_reaction("✅")
        await confirmation_message.add_reaction("❌")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            if str(reaction.emoji) == "✅":
                self.qlist.add_user_question({"question": question, "user_id": ctx.author.id})
                await ctx.send("Question submitted successfully!", delete_after=10)
            else:
                await ctx.send("Question submission canceled.", delete_after=10)
        except asyncio.TimeoutError:
            await ctx.send("No response received, question submission canceled.", delete_after=10)
        finally:
            await confirmation_message.delete()
        await ctx.message.delete()

    @question.command(name="list")
    async def list_questions(self, ctx):
        """List your submitted questions"""
        user_questions = self.qlist.get_user_questions(ctx.author.id)
        if not user_questions:
            await ctx.author.send("You have no submitted questions.")
            return

        embeds = []
        for question in user_questions:
            embed = discord.Embed(
                description=f"> {question['question']}",
                color=0x6EDFBA
            )
            embeds.append(embed)

        await menu(ctx, embeds, DEFAULT_CONTROLS, timeout=60.0)

    @question.command(name="check")
    @commands.admin_or_permissions(manage_guild=True)
    async def check_questions(self, ctx):
        """Check all user submitted questions"""
        user_questions = self.qlist.user_submitted_questions
        if not user_questions:
            await ctx.author.send("There are no user submitted questions.")
            return

        embeds = []
        for question in user_questions:
            embed = discord.Embed(
                description=f"**User:** <@{question['user_id']}>\n**Question:** {question['question']}",
                color=0x6EDFBA
            )
            embeds.append(embed)

        await menu(ctx, embeds, DEFAULT_CONTROLS, timeout=60.0)

    @question.command(name="setskip")
    @commands.admin_or_permissions(manage_guild=True)
    async def set_skip(self, ctx, votes: int):
        """Set the number of skip votes needed to skip a question"""
        await self.config.guild(ctx.guild).skip_votes_required.set(votes)
        await ctx.send(f"Skip votes required set to {votes}")

    @question.command(name="test")
    @commands.admin_or_permissions(manage_guild=True)
    async def test_question(self, ctx):
        """Ask a test question immediately"""
        channel_id = await self.config.guild(ctx.guild).channel_id()
        channel = self.bot.get_channel(channel_id)
        if not channel:
            await ctx.send("Channel not set.")
            return
        await self.ask_question(channel)

class SkipVoteView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.skip_votes = 0
        self.skip_voters = set()

    @discord.ui.button(label="Skip Vote: 0", style=discord.ButtonStyle.gray)
    async def skip_vote_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        user = interaction.user

        if user.id in self.skip_voters:
            await interaction.response.send_message("You have already voted to skip this question.", ephemeral=True)
            return

        self.skip_voters.add(user.id)
        self.skip_votes += 1
        button.label = f"Skip Vote: {self.skip_votes}"
        await interaction.response.edit_message(view=self)

        skip_votes_required = await self.cog.config.guild(interaction.guild).skip_votes_required()
        if self.skip_votes >= skip_votes_required:
            self.skip_votes = 0
            self.skip_voters = set()
            await self.cog.ask_question(interaction.channel)
            await interaction.response.send_message("Skipping the question...", ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(DailyQ(bot))
