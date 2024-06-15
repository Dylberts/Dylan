import discord
from redbot.core import commands
import random
import asyncio
from PIL import Image, ImageDraw, ImageFont
import io

class Quote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.recent_messages = {}
        self.cache = {}

    async def cache_messages(self):
        await self.bot.wait_until_ready()
        while True:
            for guild in self.bot.guilds:
                messages = []
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).read_message_history:
                        async for message in channel.history(limit=100):
                            if not message.author.bot:
                                messages.append(message)
                self.recent_messages[guild.id] = messages
            await asyncio.sleep(300)  # Update every 5 minutes

    @commands.command(name="quote")
    async def random_quote(self, ctx):
        if ctx.guild.id not in self.recent_messages or not self.recent_messages[ctx.guild.id]:
            await ctx.send("No quotes found.")
            return

        message = random.choice(self.recent_messages[ctx.guild.id])
        img = self.get_cached_image(message.content, message.author.display_name)

        with io.BytesIO() as image_binary:
            img.save(image_binary, 'PNG')
            image_binary.seek(0)
            file = discord.File(fp=image_binary, filename='quote.png')

        embed = discord.Embed(color=0x6EDFBA)
        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
        embed.set_footer(text=f"Message from {message.channel.name}")
        embed.set_image(url="attachment://quote.png")
        
        await ctx.send(file=file, embed=embed)

    @commands.command(name="rquote")
    async def random_funny_quote(self, ctx):
        users = [member.display_name for member in ctx.guild.members if not member.bot]
        quotes = [
            "Life is like a box of chocolates. You never know what you're gonna get.",
            "I'm not arguing, I'm just explaining why I'm right.",
            "The early bird can have the worm, because worms are gross and mornings are stupid.",
            "I'm on a seafood diet. I see food, and I eat it.",
            "I would challenge you to a battle of wits, but I see you are unarmed."
        ]

        compliments = [
            "You're a great person, {user}!",
            "{user}, you light up the room!",
            "You're awesome, {user}!",
        ]

        insults = [
            "{user}, you're like a cloud. When you disappear, it's a beautiful day.",
            "I'd agree with you {user}, but then we'd both be wrong.",
            "{user}, if I had a dollar for every time you said something smart, I'd be broke.",
        ]

        if users:
            user = random.choice(users)
            choice = random.choice(quotes + [compliment.format(user=user) for compliment in compliments] + [insult.format(user=user) for insult in insults])
        else:
            choice = random.choice(quotes)

        img = self.get_cached_image(choice, "Random Quote")

        with io.BytesIO() as image_binary:
            img.save(image_binary, 'PNG')
            image_binary.seek(0)
            file = discord.File(fp=image_binary, filename='quote.png')

        embed = discord.Embed(color=0x6EDFBA)
        embed.set_image(url="attachment://quote.png")
        
        await ctx.send(file=file, embed=embed)

    def get_cached_image(self, text, author):
        key = (text, author)
        if key not in self.cache:
            self.cache[key] = self.create_image(text, author)
        return self.cache[key]

    def create_image(self, text, author):
        width, height = 800, 200
        background_color = (245, 245, 245)
        text_color = (0, 0, 0)
        font_path = "arial.ttf"  # Ensure the path to your font file is correct
        font_size = 24

        img = Image.new('RGB', (width, height), color=background_color)
        d = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            font = ImageFont.load_default()

        text_position = (20, 50)
        author_position = (20, 150)
        d.text(text_position, text, fill=text_color, font=font)
        d.text(author_position, f"- {author}", fill=text_color, font=font)

        return img

    def cog_unload(self):
        self.bot.loop.create_task(self.cache_messages_task.cancel())

def setup(bot):
    cog = Quote(bot)
    bot.add_cog(cog)
    bot.loop.create_task(cog.cache_messages())
