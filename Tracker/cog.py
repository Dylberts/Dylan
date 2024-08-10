import discord
from redbot.core import commands, Config
from datetime import datetime
import aiohttp
import os
from tempfile import TemporaryDirectory

class Tracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(enabled=False, report_channel=None, exempt_channels=[])
        self.temp_dir = TemporaryDirectory()  # Temporary directory for image downloads

    def cog_unload(self):
        self.temp_dir.cleanup()  # Clean up the temporary directory when the cog is unloaded

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.__class__.__name__} is ready.')

    @commands.group()
    async def tracker(self, ctx):
        """Commands for the Tracker cog."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid tracker command passed.")

    @tracker.command()
    async def enable(self, ctx):
        """Enable the Tracker cog."""
        await self.config.enabled.set(True)
        await ctx.send("Tracker enabled.")

    @tracker.command()
    async def disable(self, ctx):
        """Disable the Tracker cog."""
        await self.config.enabled.set(False)
        await ctx.send("Tracker disabled.")

    @tracker.command()
    async def report(self, ctx, channel: discord.TextChannel):
        """Set the reporting channel."""
        await self.config.report_channel.set(channel.id)
        await ctx.send(f"Reporting channel set to {channel.mention}.")

    @tracker.command()
    async def exempt(self, ctx, channel: discord.TextChannel):
        """Exempt a channel from tracking."""
        exempt_channels = await self.config.exempt_channels()
        if channel.id not in exempt_channels:
            exempt_channels.append(channel.id)
            await self.config.exempt_channels.set(exempt_channels)
            await ctx.send(f"{channel.mention} added to exempt channels.")
        else:
            await ctx.send(f"{channel.mention} is already an exempt channel.")

    @tracker.command()
    async def scrub(self, ctx, user: discord.User):
        """Scrub all reports of a specific user."""
        report_channel_id = await self.config.report_channel()
        if report_channel_id:
            report_channel = self.bot.get_channel(report_channel_id)
            if report_channel:
                async for message in report_channel.history(limit=None):
                    if message.embeds:
                        embed = message.embeds[0]
                        if embed.footer and embed.footer.text == str(user.id):
                            await message.delete()
                await ctx.send(f"All reports for {user.mention} have been scrubbed.")
            else:
                await ctx.send("Reporting channel not set.")
        else:
            await ctx.send("Reporting channel not set.")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        enabled = await self.config.enabled()
        if not enabled:
            return

        if before.author.bot:
            return

        exempt_channels = await self.config.exempt_channels()
        if before.channel.id in exempt_channels:
            return

        report_channel_id = await self.config.report_channel()
        if report_channel_id:
            report_channel = self.bot.get_channel(report_channel_id)
            if report_channel:
                embed = discord.Embed(
                    title="Message Edited",
                    color=0x6EDFBA,
                )
                embed.set_thumbnail(url=before.author.avatar.url)
                embed.add_field(name="User", value=f"{before.author.mention}", inline=False)
                embed.add_field(name="Original Message", value=f"> {before.content}", inline=False)
                embed.add_field(name="Edited Message", value=f"[Click here to view edited message](<{after.jump_url}>)", inline=False)

                await report_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        enabled = await self.config.enabled()
        if not enabled:
            return

        if message.author.bot:
            return

        exempt_channels = await self.config.exempt_channels()
        if message.channel.id in exempt_channels:
            return

        report_channel_id = await self.config.report_channel()
        if report_channel_id:
            report_channel = self.bot.get_channel(report_channel_id)
            if report_channel:
                embed = discord.Embed(
                    title="Message Deleted",
                    color=0x6EDFBA,
                )
                embed.set_thumbnail(url=message.author.avatar.url)
                embed.add_field(name="User", value=f"{message.author.mention}", inline=False)

                if message.content:
                    embed.add_field(name="Original Message", value=f"> {message.content}", inline=False)

                # Handle image or video attachments
                if message.attachments:
                    for attachment in message.attachments:
                        if attachment.content_type and ('image' in attachment.content_type or 'video' in attachment.content_type):
                            file_path = await self.download_file(attachment.url, attachment.filename)
                            if file_path:
                                file = discord.File(file_path)
                                embed.set_image(url=f"attachment://{attachment.filename}")
                                await report_channel.send(embed=embed, file=file)
                                os.remove(file_path)  # Clean up the file after sending
                            else:
                                await report_channel.send(embed=embed)
                        else:
                            await report_channel.send(embed=embed)
                else:
                    await report_channel.send(embed=embed)

    async def download_file(self, url, filename):
        """Download a file from a given URL and save it locally."""
        file_path = os.path.join(self.temp_dir.name, filename)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        with open(file_path, 'wb') as f:
                            f.write(await response.read())
                        return file_path
        except Exception as e:
            print(f"Failed to download {url}: {e}")
        return None

async def setup(bot):
    await bot.add_cog(Tracker(bot))
