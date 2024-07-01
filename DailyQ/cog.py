import discord
import random
import asyncio
from redbot.core import commands, Config, checks
from redbot.core.bot import Red
from redbot.core.commands import Context
from datetime import datetime, timedelta
import importlib.util
import os

class DailyQ(commands.Cog):
    """Cog to ask a daily question in a specified channel."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "channel_id": None,
            "member_questions": [],
            "asked_member_questions": [],
            "frequency": 24,  # Default to 24 hours
            "submissions": {},  # Track submissions per user
            "last_reset": None,  # Track the last reset time
            "asked_qlist_questions": [],  # Track asked Qlist questions
            "skip_threshold": 4  # Default skip threshold
        }
        self.config.register_guild(**default_guild)
        self.ask_question_task = self.bot.loop.create_task(self.ask_question_task())
        self.reset_submissions_task = self.bot.loop.create_task(self.reset_submissions_task())

        # Load Qlist.py from the DailyQ folder
        cog_dir = os.path.dirname(os.path.abspath(__file__))
        qlist_path = os.path.join(cog_dir, 'Qlist.py')
        spec = importlib.util.spec_from_file_location("Qlist", qlist_path)
        self.Qlist = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.Qlist)

    def cog_unload(self):
        self.ask_question_task.cancel()
        self.reset_submissions_task.cancel()

    @commands.group()
    async def question(self, ctx: Context):
        """Group command for daily question related subcommands."""
        pass

    @question.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def setchannel(self, ctx: Context, channel: discord.abc.GuildChannel, message_id: int = None):
        """Set the channel, thread, or a specific post within a forum channel where the daily question will be asked."""
        if isinstance(channel, (discord.TextChannel, discord.Thread)):
            await self.config.guild(ctx.guild).channel_id.set(channel.id)
            await self.config.guild(ctx.guild).message_id.set(message_id)
            location_msg = f"The daily question location has been set to {channel.mention}"
            if message_id:
                location_msg += f" with message ID {message_id}"
            await ctx.send(location_msg)
        elif isinstance(channel, discord.ForumChannel):
            if message_id:
                # Validate that the message ID is in a thread of the forum
                thread = None
                for thread in channel.threads:
                    try:
                        message = await thread.fetch_message(message_id)
                        break
                    except discord.NotFound:
                        continue
                if thread and message:
                    await self.config.guild(ctx.guild).channel_id.set(thread.id)
                    await self.config.guild(ctx.guild).message_id.set(message_id)
                    await ctx.send(f"The daily question location has been set to the post in {thread.mention} with message ID {message_id}")
                else:
                    await ctx.send("The specified message ID was not found in any thread within the forum channel.")
            else:
                await ctx.send("For forum channels, you must specify a message ID within a thread.")
        else:
            await ctx.send("The specified channel must be a text channel, thread, or forum channel.")

    @question.command()
    async def ask(self, ctx: Context, *, question: str):
        """Submit a question to be asked."""
        await ctx.message.delete()  # Delete the user's message immediately

        guild_config = await self.config.guild(ctx.guild).all()
        user_id = str(ctx.author.id)
        now = datetime.utcnow()

        # Reset submissions if it's a new day
        if guild_config["last_reset"]:
            last_reset = datetime.fromisoformat(guild_config["last_reset"])
            if now - last_reset > timedelta(days=1):
                guild_config["submissions"] = {}
                guild_config["last_reset"] = now.isoformat()
                await self.config.guild(ctx.guild).set(guild_config)

        submissions = guild_config["submissions"]
        user_submissions = submissions.get(user_id, 0)

        if user_submissions >= 3:
            await ctx.send("You have already submitted 3 questions today. Please wait until tomorrow to submit more.")
            return

        # Ask for confirmation
        confirm_message = await ctx.send("Are you sure you want to submit this question? React with ✅ to confirm or ❌ to cancel.")
        await confirm_message.add_reaction("✅")
        await confirm_message.add_reaction("❌")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
            if str(reaction.emoji) == "✅":
                async with self.config.guild(ctx.guild).member_questions() as member_questions:
                    member_questions.append(question)

                submissions[user_id] = user_submissions + 1
                await self.config.guild(ctx.guild).submissions.set(submissions)

                if not guild_config["last_reset"]:
                    await self.config.guild(ctx.guild).last_reset.set(now.isoformat())

                await ctx.send("Your question has been submitted!")
            else:
                await ctx.send("Your question submission has been canceled.")
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Please try again.")

        await confirm_message.delete(delay=10)

    @question.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def setfrequency(self, ctx: Context, hours: int):
        """Set the frequency of how often a question is asked (in hours)."""
        if hours < 1:
            await ctx.send("Frequency must be at least 1 hour.")
            return
        
        await self.config.guild(ctx.guild).frequency.set(hours)
        self.ask_question_task.cancel()
        self.ask_question_task = self.bot.loop.create_task(self.ask_question_task())
        await ctx.send(f"The question frequency has been set to every {hours} hours.")

    @question.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def testq(self, ctx: Context):
        """Ask a test question immediately without affecting the daily question timer or queue."""
        guild_config = await self.config.guild(ctx.guild).all()
        channel_id = guild_config["channel_id"]
        member_questions = guild_config["member_questions"]
        asked_member_questions = guild_config["asked_member_questions"]
        asked_qlist_questions = guild_config["asked_qlist_questions"]
        channel = self.bot.get_channel(channel_id) or self.bot.get_thread(channel_id)

        if not channel_id or not channel:
            await ctx.send("The daily question location is not set or cannot be found.")
            return

        if member_questions:
            question = random.choice(member_questions)
        else:
            available_qlist_questions = [q for q in self.Qlist.questions if q not in asked_qlist_questions]
            if not available_qlist_questions:
                # Reset asked_qlist_questions if all have been asked
                asked_qlist_questions = []
                available_qlist_questions = self.Qlist.questions
            question = random.choice(available_qlist_questions)

        embed = discord.Embed(title="**DAILY QUESTION 💬**", description=f"> *{question}*\n\n", color=0x6EDFBA)
        embed.set_footer(text="Try `!question ask` to submit your own questions")
        view = SkipView(self)
        await channel.send(embed=embed, view=view)

    async def ask_question_task(self):
        while True:
            await self.bot.wait_until_ready()
            for guild in self.bot.guilds:
                config = await self.config.guild(guild).all()
                channel_id = config["channel_id"]
                member_questions = config["member_questions"]
                asked_member_questions = config["asked_member_questions"]
                asked_qlist_questions = config["asked_qlist_questions"]

                if not channel_id:
                    continue

                channel = self.bot.get_channel(channel_id) or self.bot.get_thread(channel_id)
                if not channel:
                    continue

                if member_questions:
                    question = random.choice(member_questions)
                    member_questions.remove(question)
                    asked_member_questions.append(question)
                else:
                    available_qlist_questions = [q for q in self.Qlist.questions if q not in asked_qlist_questions]
                    if not available_qlist_questions:
                        # Reset asked_qlist_questions if all have been asked
                        asked_qlist_questions = []
                        available_qlist_questions = self.Qlist.questions
                    question = random.choice(available_qlist_questions)
                    asked_qlist_questions.append(question)

                await self.config.guild(guild).member_questions.set(member_questions)
                await self.config.guild(guild).asked_member_questions.set(asked_member_questions)
                await self.config.guild(guild).asked_qlist_questions.set(asked_qlist_questions)

                embed = discord.Embed(title="**DAILY QUESTION 💬**", description=f"> *{question}*\n\n", color=0x6EDFBA)
                embed.set_footer(text="Try `!question ask` to submit your own questions")
                view = SkipView(self)
                message = await channel.send(embed=embed, view=view)
                view.message = message  # Store the sent message in the view for later deletion
                await self.config.guild(guild).set_raw("current_question_message_id", value=message.id)
                
            await asyncio.sleep(24 * 60 * 60)

    async def reset_submissions_task(self):
        while True:
            await self.bot.wait_until_ready()
            now = datetime.utcnow()
            for guild in self.bot.guilds:
                guild_config = await self.config.guild(guild).all()
                last_reset = guild_config["last_reset"]

                if not last_reset or (now - datetime.fromisoformat(last_reset)) > timedelta(days=1):
                    await self.config.guild(guild).submissions.set({})
                    await self.config.guild(guild).last_reset.set(now.isoformat())
            await asyncio.sleep(24 * 60 * 60)

    @question.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def setskip(self, ctx: Context, threshold: int):
        """Set the number of votes needed to skip a question."""
        if threshold < 1:
            await ctx.send("The skip threshold must be at least 1.")
            return
        await self.config.guild(ctx.guild).skip_threshold.set(threshold)
        await ctx.send(f"The skip threshold has been set to {threshold} votes.")

class SkipButton(discord.ui.Button):
    def __init__(self, cog, style=discord.ButtonStyle.secondary):
        super().__init__(label="Skip Question", style=style)
        self.cog = cog
        self.votes = set()

    async def callback(self, interaction: discord.Interaction):
        guild_config = await self.cog.config.guild(interaction.guild).all()
        skip_threshold = guild_config["skip_threshold"]
        user_id = interaction.user.id

        if user_id in self.votes:
            await interaction.response.send_message("You've already voted to skip this question", ephemeral=True)
            return

        self.votes.add(user_id)
        self.label = f"Skip Question ({len(self.votes)})"
        await interaction.response.edit_message(view=self.view)

        if len(self.votes) >= skip_threshold:
            await interaction.followup.send("The question has been skipped. Asking a new question...", ephemeral=True)
            await self.cog.skip_question(interaction.message)

class SkipView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.message = None
        self.add_item(SkipButton(cog))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True

async def skip_question(self, message):
    await message.delete()

    guild_config = await self.config.guild(message.guild).all()
    channel_id = guild_config["channel_id"]
    member_questions = guild_config["member_questions"]
    asked_member_questions = guild_config["asked_member_questions"]
    asked_qlist_questions = guild_config["asked_qlist_questions"]
    channel = self.bot.get_channel(channel_id) or self.bot.get_thread(channel_id)

    if not channel_id or not channel:
        return

    if member_questions:
        question = random.choice(member_questions)
        member_questions.remove(question)
        asked_member_questions.append(question)
    else:
        available_qlist_questions = [q for q in self.Qlist.questions if q not in asked_qlist_questions]
        if not available_qlist_questions:
            # Reset asked_qlist_questions if all have been asked
            asked_qlist_questions = []
            available_qlist_questions = self.Qlist.questions
        question = random.choice(available_qlist_questions)
        asked_qlist_questions.append(question)

    await self.config.guild(message.guild).member_questions.set(member_questions)
    await self.config.guild(message.guild).asked_member_questions.set(asked_member_questions)
    await self.config.guild(message.guild).asked_qlist_questions.set(asked_qlist_questions)

    embed = discord.Embed(title="**DAILY QUESTION 💬**", description=f"> *{question}*\n\n", color=0x6EDFBA)
    embed.set_footer(text="Try `!question ask` to submit your own questions")
    view = SkipView(self)
    new_message = await channel.send(embed=embed, view=view)
    view.message = new_message  # Store the new message in the view for future reference
    await self.config.guild(message.guild).set_raw("current_question_message_id", value=new_message.id)

def setup(bot: Red):
    bot.add_cog(DailyQ(bot))
