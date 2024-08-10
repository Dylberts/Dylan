import discord
from redbot.core import commands, Config
import aiohttp
import os

class Tracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(enabled=False, report_channel=None, exempt_channels=[])
        self.temp_folder = os.path.join(os.getcwd(), "temp_photo_tracking")  # Use an absolute path

        try:
            # Ensure the temporary folder exists
            if not os.path.exists(self.temp_folder):
                os.makedirs(self.temp_folder)
        except PermissionError as e:
            print(f"Permission error while creating temp folder: {e}")
        except Exception as e:
            print(f"Unexpected error while creating temp folder: {e}")
        
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
                    color=0x6EDFBA
                )
                embed.set_thumbnail(url=message.author.avatar.url)
                embed.add_field(name="User", value=f"{message.author.mention}", inline=False)
                if message.content:
                    embed.add_field(name="Original Message", value=f"> {message.content}", inline=False)

                # If the message had an attachment (image/video), download and include it
                if message.attachments:
                    attachment = message.attachments[0]
                    file_path = await self.download_attachment(attachment)
                    if file_path:
                        file = discord.File(file_path)
                        embed.set_image(url=f"attachment://{attachment.filename}")
                        await report_channel.send(embed=embed, file=file)
                        os.remove(file_path)  # Clean up the file after sending
                    else:
                        await report_channel.send(embed=embed)
                else:
                    await report_channel.send(embed=embed)

    async def download_attachment(self, attachment):
        """Download the attachment and save it locally."""
        file_path = os.path.join(self.temp_folder, attachment.filename)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as response:
                    if response.status == 200:
                        with open(file_path, 'wb') as f:
                            f.write(await response.read())
                        return file_path
        except Exception as e:
            print(f"Failed to download {attachment.url}: {e}")
        return None

async def setup(bot):
    await bot.add_cog(Tracker(bot))
