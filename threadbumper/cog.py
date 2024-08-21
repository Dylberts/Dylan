from redbot.core import commands, checks, Config
from redbot.core.bot import Red
from discord import Thread
import asyncio

class ThreadBumper(commands.Cog):
    """Cog to keep threads alive by silently bumping them."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Corrected syntax
        self.config.register_guild(enabled=True)
        self.bumping_tasks = {}

    async def initialize_bumper(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            enabled = await self.config.guild(guild).enabled()
            if enabled or enabled is None:
                await self.config.guild(guild).enabled.set(True)  # Set to True by default
                if guild.id not in self.bumping_tasks:
                    self.bumping_tasks[guild.id] = self.bot.loop.create_task(self.bump_threads(guild))

    @commands.group()
    @commands.guild_only()
    @checks.admin()
    async def threadbumper(self, ctx):
        """Commands to manage the thread bumper."""
        pass

    @threadbumper.command(name="enable")
    async def enable_bumper(self, ctx):
        """Enable the thread bumper."""
        await self.config.guild(ctx.guild).enabled.set(True)
        await ctx.send("Understood! Thread bumper is now: **enabled**.")
        if ctx.guild.id not in self.bumping_tasks:
            self.bumping_tasks[ctx.guild.id] = self.bot.loop.create_task(self.bump_threads(ctx.guild))

    @threadbumper.command(name="disable")
    async def disable_bumper(self, ctx):
        """Disable the thread bumper."""
        await self.config.guild(ctx.guild).enabled.set(False)
        await ctx.send("Understood! Thread bumper is now: **disabled**.")
        if ctx.guild.id in self.bumping_tasks:
            self.bumping_tasks[ctx.guild.id].cancel()
            del self.bumping_tasks[ctx.guild.id]

    async def bump_threads(self, guild):
        await self.bot.wait_until_ready()
        while await self.config.guild(guild).enabled():
            for channel in guild.text_channels:
                if not await self.config.guild(guild).enabled():
                    break
                for thread in channel.threads:
                    if not thread.locked and not thread.archived:
                        try:
                            await thread.edit(name=thread.name + ' ')
                            await asyncio.sleep(5)  # Sleep to avoid rate limiting
                        except:
                            pass  # Handle any exceptions if the thread can't be edited
                for thread in channel.threads:  # Check private threads as well
                    if thread.is_private() and not thread.locked and not thread.archived:
                        try:
                            await thread.edit(name=thread.name + ' ')
                            await asyncio.sleep(5)  # Sleep to avoid rate limiting
                        except:
                            pass  # Handle any exceptions if the thread can't be edited
            await asyncio.sleep(71 * 60 * 60)  # Check every 71 hours

    def cog_unload(self):
        for task in self.bumping_tasks.values():
            task.cancel()

    async def cog_load(self):
        await self.initialize_bumper()
