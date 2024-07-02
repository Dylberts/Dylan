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
            "skip_threshold": 4,  # Default skip threshold
            "current_question_message_id": None  # Store the current question message ID
        }
        self.config.register_guild(**default_guild)
        self.just_loaded = True  # Add a flag to check if the cog was just loaded
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

    @commands.group(aliases=['q'])
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
            await ctx.send(location_msg, delete_after=15)
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
                    await ctx.send(f"The daily question location has been set to the post in {thread.mention} with message ID {message_id}", delete_after=15)
                else:
                    await ctx.send("The specified message ID was not found in any thread within the forum channel.", delete_after=15)
            else:
                await ctx.send("For forum channels, you must specify a message ID within a thread.", delete_after=15)
        else:
            await ctx.send("The specified channel must be a text channel, thread, or forum channel.", delete_after=15)

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
            await ctx.send("You have already submitted 3 questions today. Please wait until tomorrow to submit more.", delete_after=15)
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

                await ctx.send("Your question has been submitted!", delete_after=15)
            else:
                await ctx.send("Your question submission has been canceled.", delete_after=15)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Please try again.", delete_after=15)

        await confirm_message.delete(delay=15)

    @question.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def setfrequency(self, ctx: Context, hours: int):
        """Set the frequency of how often a question is asked (in hours)."""
        if hours < 1:
            await ctx.send("Frequency must be at least 1 hour.", delete_after=15)
            return
        
        await self.config.guild(ctx.guild).frequency.set(hours)
        self.ask_question_task.cancel()
        self.ask_question_task = self.bot.loop.create_task(self.ask_question_task())
        await ctx.send(f"The question frequency has been set to every {hours} hours.", delete_after=15)

    @question.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def testq(self, ctx: Context):
        """Ask a test question immediately without affecting the daily question timer or queue."""
        guild_config = await self.config.guild(ctx.guild).all()
        member_questions = guild_config["member_questions"]
        asked_qlist_questions = guild_config["asked_qlist_questions"]

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
        await ctx.send(embed=embed)

    @question.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def viewsubmissions(self, ctx: Context):
        """View all member-submitted questions."""
        member_questions = await self.config.guild(ctx.guild).member_questions()
        if not member_questions:
            await ctx.send("There are no submitted questions.", delete_after=15)
            return

        questions_list = "\n".join([f"{idx + 1}. {question}" for idx, question in enumerate(member_questions)])
        await ctx.send(f"**Submitted Questions:**\n{questions_list}", delete_after=15)

    @question.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def removememberquestion(self, ctx: Context, index: int):
        """Remove a member-submitted question by index."""
        async with self.config.guild(ctx.guild).member_questions() as member_questions:
            if 0 < index <= len(member_questions):                
                removed_question = member_questions.pop(index - 1)
                await ctx.send(f"Removed question: {removed_question}", delete_after=15)
            else:
                await ctx.send("Invalid index provided.", delete_after=15)

    @question.command()
    async def myquestions(self, ctx: Context):
        """View your submitted questions."""
        guild_config = await self.config.guild(ctx.guild).all()
        user_id = str(ctx.author.id)
        submissions = guild_config["submissions"]

        if user_id not in submissions:
            await ctx.send("You haven't submitted any questions yet.", ephemeral=True)
            return

        member_questions = guild_config["member_questions"]
        user_questions = [q for q in member_questions if q["user_id"] == user_id]

        if not user_questions:
            await ctx.send("You don't have any questions in the queue.", ephemeral=True)
            return

        questions_list = "\n".join([f"{idx + 1}. {question['text']}" for idx, question in enumerate(user_questions)])
        await ctx.send(f"**Your Submitted Questions:**\n{questions_list}", ephemeral=True)

    @question.command()
    async def editquestion(self, ctx: Context, index: int, *, new_question: str):
        """Edit your submitted question by index."""
        guild_config = await self.config.guild(ctx.guild).all()
        user_id = str(ctx.author.id)
        submissions = guild_config["submissions"]

        if user_id not in submissions:
            await ctx.send("You haven't submitted any questions yet.", ephemeral=True)
            return

        async with self.config.guild(ctx.guild).member_questions() as member_questions:
            user_questions = [q for q in member_questions if q["user_id"] == user_id]

            if 0 < index <= len(user_questions):
                question_to_edit = user_questions[index - 1]
                question_to_edit["text"] = new_question
                await ctx.send(f"Your question has been edited to: {new_question}", ephemeral=True)
            else:
                await ctx.send("Invalid index provided.", ephemeral=True)

    @question.command()
    async def deletequestion(self, ctx: Context, index: int):
        """Delete your submitted question by index."""
        guild_config = await self.config.guild(ctx.guild).all()
        user_id = str(ctx.author.id)
        submissions = guild_config["submissions"]

        if user_id not in submissions:
            await ctx.send("You haven't submitted any questions yet.", ephemeral=True)
            return

        async with self.config.guild(ctx.guild).member_questions() as member_questions:
            user_questions = [q for q in member_questions if q["user_id"] == user_id]

            if 0 < index <= len(user_questions):
                removed_question = user_questions.pop(index - 1)
                await ctx.send(f"Removed your question: {removed_question['text']}", ephemeral=True)
            else:
                await ctx.send("Invalid index provided.", ephemeral=True)

    async def ask_question_task(self):
        while True:
            await self.bot.wait_until_ready()
            if self.just_loaded:  # Skip asking a question if the cog was just loaded
                self.just_loaded = False
                await asyncio.sleep(10)  # Give some time before checking again
                continue

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
                
                # Send the embed with an interactive button for skipping
                message = await channel.send(embed=embed, components=[[
                    discord.ui.Button(style=discord.ButtonStyle.grey, label="Skip Question", custom_id="skip_question")
                ]])

                await self.config.guild(guild).current_question_message_id.set(message.id)
                await self.config.guild(guild).skip_votes.set({})

            frequency = (await self.config.guild(guild).frequency()) * 3600  # Convert hours to seconds
            await asyncio.sleep(frequency)

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

    @commands.Cog.listener()
    async def on_button_click(self, interaction: discord.Interaction):
        if interaction.custom_id != "skip_question":
            return

        guild_id = interaction.guild_id
        user_id = str(interaction.user.id)

        config = await self.config.guild_from_id(guild_id).all()
        skip_votes = config.get("skip_votes", {})

        if user_id in skip_votes:
            await interaction.response.send_message("You have already voted to skip this question.", ephemeral=True)
            return

        skip_votes[user_id] = True
        await self.config.guild_from_id(guild_id).skip_votes.set(skip_votes)

        skip_threshold = config.get("skip_threshold", 4)
        current_vote_count = len(skip_votes)

        if current_vote_count < skip_threshold:
            await interaction.response.edit_message(
                components=[[
                    discord.ui.Button(
                        style=discord.ButtonStyle.grey,
                        label=f"Skip Question ({current_vote_count})",
                        custom_id="skip_question"
                    )
                ]]
            )
        else:
            current_question_message_id = config["current_question_message_id"]
            channel_id = config["channel_id"]
            channel = self.bot.get_channel(channel_id) or self.bot.get_thread(channel_id)
            if channel and current_question_message_id:
                try:
                    message = await channel.fetch_message(current_question_message_id)
                    await message.delete()
                except discord.NotFound:
                    pass

            if config["member_questions"]:
                question = random.choice(config["member_questions"])
                config["member_questions"].remove(question)
                config["asked_member_questions"].append(question)
            else:
                available_qlist_questions = [q for q in self.Qlist.questions if q not in config["asked_qlist_questions"]]
                if not available_qlist_questions:
                    config["asked_qlist_questions"] = []
                    available_qlist_questions = self.Qlist.questions
                question = random.choice(available_qlist_questions)
                config["asked_qlist_questions"].append(question)

            await self.config.guild_from_id(guild_id).set(config)

            embed = discord.Embed(title="**DAILY QUESTION 💬**", description=f"> *{question}*\n\n", color=0x6EDFBA)
            embed.set_footer(text="Try `!question ask` to submit your own questions")
            new_message = await channel.send(embed=embed, components=[[
                discord.ui.Button(style=discord.ButtonStyle.grey, label="Skip Question", custom_id="skip_question")
            ]])

            await self.config.guild_from_id(guild_id).current_question_message_id.set(new_message.id)
            await self.config.guild_from_id(guild_id).skip_votes.set({})

    @question.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def setskip(self, ctx: Context, skip_count: int):
        """Set the number of votes required to skip a question."""
        if skip_count < 1:
            await ctx.send("Skip count must be at least 1.", delete_after=15)
            return
        
        await self.config.guild(ctx.guild).skip_threshold.set(skip_count)
        await ctx.send(f"The skip threshold has been set to {skip_count} votes.", delete_after=15)

def setup(bot: Red):
    bot.add_cog(DailyQ(bot))

