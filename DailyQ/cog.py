import discord
import random
import aiohttp
from redbot.core import commands, Config, checks
from redbot.core.bot import Red
from redbot.core.commands import Context
from redbot.core.utils import get_end_user_data_statement, mod
from datetime import datetime, timedelta
from redbot.core.utils import bounded_gather

class DailyQ(commands.Cog):
    """Cog to ask a daily question in a specified channel."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "channel_id": None,
            "questions": [],
            "asked_questions": [],
            "frequency": 24,  # Default to 24 hours
            "submissions": {},  # Track submissions per user
            "last_reset": None  # Track the last reset time
        }
        self.config.register_guild(**default_guild)
        self.ask_question_task = self.bot.loop.create_task(self.ask_question_task())
        self.reset_submissions_task = self.bot.loop.create_task(self.reset_submissions_task())

    def cog_unload(self):
        self.ask_question_task.cancel()
        self.reset_submissions_task.cancel()

    @commands.group()
    async def question(self, ctx: Context):
        """Group command for daily question related subcommands."""
        pass

    @question.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def setchannel(self, ctx: Context, channel: discord.TextChannel):
        """Set the channel where the daily question will be asked."""
        await self.config.guild(ctx.guild).channel_id.set(channel.id)
        await ctx.send(f"The daily question channel has been set to {channel.mention}")

    @question.command()
    async def ask(self, ctx: Context, *, question: str):
        """Submit a question to be asked."""
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

        async with self.config.guild(ctx.guild).questions() as questions:
            questions.append(question)

        submissions[user_id] = user_submissions + 1
        await self.config.guild(ctx.guild).submissions.set(submissions)

        if not guild_config["last_reset"]:
            await self.config.guild(ctx.guild).last_reset.set(now.isoformat())

        await ctx.send("Your question has been submitted!")

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
        questions = guild_config["questions"]
        channel = self.bot.get_channel(channel_id)

        if not channel_id or not channel:
            await ctx.send("The daily question channel is not set or cannot be found.")
            return

        if questions:
            question = random.choice(questions)
        else:
            question = await self.generate_random_question()

        await channel.send(f"Test Question: {question}")
        await ctx.send("A test question has been sent.")

    async def ask_question_task(self):
        while True:
            await self.bot.wait_until_ready()
            for guild in self.bot.guilds:
                config = await self.config.guild(guild).all()
                channel_id = config["channel_id"]
                questions = config["questions"]
                asked_questions = config["asked_questions"]

                if not channel_id:
                    continue

                channel = self.bot.get_channel(channel_id)
                if not channel:
                    continue

                if questions:
                    question = random.choice(questions)
                    questions.remove(question)
                    asked_questions.append(question)
                else:
                    question = await self.generate_random_question()
                    asked_questions.append(question)

                await self.config.guild(guild).questions.set(questions)
                await self.config.guild(guild).asked_questions.set(asked_questions)

                await channel.send(question)
            await asyncio.sleep(24 * 60 * 60)

    async def generate_random_question(self):
        """Generate a random question using the internet."""
        async with aiohttp.ClientSession() as session:
            async with session.get('https://opentdb.com/api.php?amount=1&type=multiple') as response:
                if response.status == 200:
                    data = await response.json()
                    question = data["results"][0]["question"]
                    return question
                else:
                    return "Could not fetch a random question, please try again later."

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

def setup(bot: Red):
    bot.add_cog(DailyQ(bot))
