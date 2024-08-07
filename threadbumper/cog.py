from redbot.core import commands, checks, Config
from redbot.core.bot import Red
from discord import Thread
import asyncio

class threadbumper(commands.Cog):
    """Cog to keep threads alive by silently bumping them."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_guild(enabled=True)
        self.bumping_task = None

        # Start the bumping task if enabled
        self.bot.loop.create_task(self.initialize_bumper())

    async def initialize_bumper(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            if await self.config.guild(guild).enabled():
                if not self.bumping_task:
                    self.bumping_task = self.bot.loop.create_task(self.bump_threads(guild))

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
        if not self.bumping_task:
            self.bumping_task = self.bot.loop.create_task(self.bump_threads(ctx.guild))

    @threadbumper.command(name="disable")
    async def disable_bumper(self, ctx):
        """Disable the thread bumper."""
        await self.config.guild(ctx.guild).enabled.set(False)
        await ctx.send("Understood! Thread bumper is now: **disabled**.")
        if self.bumping_task:
            self.bumping_task.cancel()
            self.bumping_task = None

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
        if self.bumping_task:
            self.bumping_task.cancel()

def setup(bot: Red):
    bot.add_cog(threadbumper(bot))
