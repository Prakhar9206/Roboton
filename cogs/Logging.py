import discord
from discord.ext import commands
import datetime

logs_channel_id = 891165082573213756

class Logging(commands.Cog, name="Logging", command_attrs=dict(hidden=True)):
    
    def __init__(self,bot):
        self.bot = bot


    @commands.Cog.listener("on_command")
    async def whenever_command_invokes(self, ctx):
        em = discord.Embed(title=f"{ctx.author}", description=f"{ctx.message.content}")
        em.set_thumbnail(url=ctx.author.avatar.url)
        em.add_field(name="Command", value=f"{ctx.command}", inline=False)
        em.add_field(name="Channel", value=f"{ctx.channel}", inline=False)
        em.add_field(name="Server", value=f"{ctx.guild}", inline=False)
        em.timestamp = datetime.datetime.utcnow()
        logs_channel = self.bot.get_channel(logs_channel_id)
        await logs_channel.send(embed=em)
        # with open('logs.txt', 'a') as f:
        #     f.write(f"{ctx.author} used '{ctx.command}' in channel '{ctx.channel}' in the server '{ctx.guild}'\n")

def setup(bot):
    bot.add_cog(Logging(bot))
    print("Logging cog is loaded")