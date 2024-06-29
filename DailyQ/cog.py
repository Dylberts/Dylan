import discord
import random
import asyncio
from redbot.core import commands, Config, checks
from redbot.core.bot import Red
from redbot.core.commands import Context
from datetime import datetime, timedelta
import Qlist  # Importing the Qlist module

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
        channel = self.bot.get_channel(channel_id)

        if not channel_id or not channel:
            await ctx.send("The daily question channel is not set or cannot be found.")
            return

        if member_questions:
            question = random.choice(member_questions)
        else:
            question = random.choice(Qlist.questions)

        embed = discord.Embed(description=f"**Daily Question:**\n*{question}*\n\n", color=0x6EDFBA)
        embed.set_footer(text="Use `!question ask` to submit your own questions!")
        await channel.send(embed=embed)

    async def ask_question_task(self):
        while True:
            await self.bot.wait_until_ready()
            for guild in self.bot.guilds:
                config = await self.config.guild(guild).all()
                channel_id = config["channel_id"]
                member_questions = config["member_questions"]
                asked_member_questions = config["asked_member_questions"]

                if not channel_id:
                    continue

                channel = self.bot.get_channel(channel_id)
                if not channel:
                    continue

                if member_questions:
                    question = random.choice(member_questions)
                    member_questions.remove(question)
                    asked_member_questions.append(question)
                else:
                    question = random.choice(Qlist.questions)

                await self.config.guild(guild).member_questions.set(member_questions)
                await self.config.guild(guild).asked_member_questions.set(asked_member_questions)

                embed = discord.Embed(description=question, color=0x6EDFBA)
                embed.set_footer(text="Use `!question ask` to submit your own questions!")
                await channel.send(embed=embed)
            await asyncio.sleep(24 * 60 * 60)

    async def reset_submissions_task(self):
        while True:
            await self.bot.wait_until_ready()
            now = datetime.utcnow()
            for guild in self.bot.guilds:
                guild_config = await self.config.guild(guild).all()
                last_reset = guild_config["last_reset"]

                if not last_reset or (now - datetime.fromisoformat(last_reset)) > timedelta(days(1)):
                    await self.config.guild(guild).submissions.set({})
                    await self.config.guild(guild).last_reset.set(now.isoformat())
            await asyncio.sleep(24 * 60 * 60)

def setup(bot: Red):
    bot.add_cog(DailyQ(bot))
