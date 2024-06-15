import discord
from redbot.core import commands
import random
import asyncio
from PIL import Image, ImageDraw, ImageFont
import io

class Quote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="quote")
    async def random_quote(self, ctx):
        channels = [channel for channel in ctx.guild.text_channels if channel.permissions_for(ctx.guild.me).read_message_history]
        messages = []

        for channel in channels:
            async for message in channel.history(limit=100):
                if message.author.bot:
                    continue
                messages.append(message)
        
        if not messages:
            await ctx.send("No quotes found.")
            return

        message = random.choice(messages)
        img = await self.create_image(message.content, message.author)

        with io.BytesIO() as image_binary:
            img.save(image_binary, 'PNG')
            image_binary.seek(0)
            file = discord.File(fp=image_binary, filename='quote.png')

        embed = discord.Embed(color=0x6EDFBA)
        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
        embed.set_footer(text=f"Message from {message.channel.name}")
        embed.set_image(url="attachment://quote.png")
        
        await ctx.send(file=file, embed=embed)

    async def create_image(self, text, author):
        # Create an image with Pillow
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

        # Load user's avatar
        avatar_size = 128  # Adjusted size
        avatar_image = author.avatar.with_size(avatar_size)

        # Calculate the paste box coordinates
        left = 20
        top = (height - avatar_size) // 2
        right = left + avatar_size
        bottom = top + avatar_size
        paste_box = (left, top, right, bottom)

        # Paste user's avatar onto the image
        img.paste(avatar_image, paste_box)

        # Add text to image
        text_position = (180, 50)  # Adjusted position
        author_position = (180, 150)  # Adjusted position
        d.text(text_position, text, fill=text_color, font=font)
        d.text(author_position, f"- {author.display_name}", fill=text_color, font=font)

        return img

    @commands.command(name="rquote")
    async def random_funny_quote(self, ctx):
        users = [member for member in ctx.guild.members if not member.bot]
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
            choice = random.choice(quotes + [compliment.format(user=user.display_name) for compliment in compliments] + [insult.format(user=user.display_name) for insult in insults])
        else:
            choice = random.choice(quotes)

        img = await self.create_image(choice, user)

        with io.BytesIO() as image_binary:
            img.save(image_binary, 'PNG')
            image_binary.seek(0)
            file = discord.File(fp=image_binary, filename='quote.png')

        embed = discord.Embed(color=0x6EDFBA)
        embed.set_image(url="attachment://quote.png")
        
        await ctx.send(file=file, embed=embed)

def setup(bot):
    bot.add_cog(Quote(bot))
