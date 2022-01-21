import discord
from discord.ext import commands
from asyncdagpi import Client, ImageFeatures
import json

with open('config.json', 'r') as f:
    key = json.load(f)
    dagpi_token = key['DAGPI_TOKEN']
    
dagpi = Client(dagpi_token)


class Image(commands.Cog, name="Image"):
    """Some fun image editing commands."""
    
    def __init__(self,bot):
        self.bot = bot

    @commands.command()
    async def shatter(self, ctx, member: discord.Member = None):
        """Shatters someone."""
        if member is None:
            member = ctx.author
        url = str(member.avatar.replace(static_format="png", size=1024))
        img = await dagpi.image_process(ImageFeatures.shatter(), url)
        file = discord.File(fp=img.image,filename=f"shatter.{img.format}")
        await ctx.send(file=file)

    @commands.command()
    async def dm(self, ctx, member: discord.Member = None, *, text):
        """Makes a fake discord message as someone else"""
        url = str(member.avatar.replace(static_format="png", size=1024))
        img = await dagpi.image_process(ImageFeatures.discord(), text=text, url=url, username=member.name)
        file = discord.File(fp=img.image,filename=f"discord.{img.format}")
        await ctx.send(file=file)

    @commands.command()
    async def pet(self, ctx, member: discord.Member = None):
        """Makes a pet gif for someone"""
        if member is None:
            member = ctx.author
        url = str(member.avatar.replace(static_format="png", size=1024))
        img = await dagpi.image_process(ImageFeatures.petpet(), url)
        file = discord.File(fp=img.image,filename=f"pet.{img.format}")
        await ctx.send(file=file)

    @commands.command()
    async def tweet(self, ctx, member: discord.Member = None, *, text):
        """Creates a fake tweet image as someone else"""
        url = str(member.avatar.replace(static_format="png", size=1024))
        img = await dagpi.image_process(ImageFeatures.tweet(), text=text, url=url, username=member.name)
        file = discord.File(fp=img.image,filename=f"pet.{img.format}")
        await ctx.send(file=file)

    @commands.command()
    async def wanted(self, ctx, member: discord.Member = None):
        """Creates a wanted poster."""
        if member is None:
            member = ctx.author
        url = str(member.avatar.replace(static_format="png", size=1024))
        img = await dagpi.image_process(ImageFeatures.wanted(), url)
        file = discord.File(fp=img.image,filename=f"pet.{img.format}")
        await ctx.send(file=file)

    @commands.command()
    async def wasted(self, ctx, member: discord.Member = None):
        """Adds a 'wasted' label on someone."""
        if member is None:
            member = ctx.author
        url = str(member.avatar.replace(static_format="png", size=1024))
        img = await dagpi.image_process(ImageFeatures.wasted(), url)
        file = discord.File(fp=img.image,filename=f"pet.{img.format}")
        await ctx.send(file=file)

    @commands.command()
    async def bonk(self, ctx, member: discord.Member = None):
        """BONK"""
        if member is None:
            member = ctx.author
        url = str(member.avatar.replace(static_format="png", size=1024))
        img = await dagpi.image_process(ImageFeatures.bonk(), url)
        file = discord.File(fp=img.image,filename=f"pet.{img.format}")
        await ctx.send(file=file)


def setup(bot):
    bot.add_cog(Image(bot))
    print("Image cog is loaded")