from discord.ext import commands
import discord

        
async def blacklist_reason(ctx, bot):
    mycol = bot.mongo_client.discord.blacklist
    doc = await mycol.find_one({
        "user" : f"{ctx.author.id}"
    })
    if doc:
        reason = doc["reason"]
        

        em = discord.Embed(title="You have been blocked from using this bot for the following reason:")
        em.description = reason
        em.color = 0xfc0335
        await ctx.send(embed=em)
        # return False

class Suspended(commands.CheckFailure):
    # def __init__(self, ctx, bot):
    #     super().__init__()
    #     self.ctx = ctx
    #     self.bot = bot
    pass