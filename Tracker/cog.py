import discord
from redbot.core import commands, Config
from datetime import datetime

class Tracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(enabled=False, report_channel=None, exempt_channels=[])
        self.attachment_cache = {}

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
                    timestamp=datetime.utcnow()
                )
                embed.set_author(name=before.author.name, icon_url=before.author.avatar.url)
                embed.add_field(name="User ID", value=before.author.id, inline=False)
                embed.add_field(name="Original Message", value=before.content, inline=False)

                if before.attachments:
                    attachment = before.attachments[0]
                    embed.add_field(name="Original Attachment", value=f"[View Attachment]({attachment.url})", inline=False)
                    self.attachment_cache[before.id] = attachment.url

                embed.set_footer(text=str(before.author.id))
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
                    timestamp=datetime.utcnow()
                )
                embed.set_author(name=message.author.name, icon_url=message.author.avatar.url)
                embed.add_field(name="User ID", value=message.author.id, inline=False)
                embed.add_field(name="Original Message", value=message.content, inline=False)

                if message.attachments:
                    attachment_url = self.attachment_cache.pop(message.id, None)
                    if attachment_url:
                        embed.add_field(name="Original Attachment", value=f"[View Attachment]({attachment_url})", inline=False)

                embed.set_footer(text=str(message.author.id))
                await report_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Tracker(bot))
